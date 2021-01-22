import urllib.parse
from unittest import TestCase, skip

import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
from traitlets.config import LoggingConfigurable

from cs3api4lab import CS3APIsManager
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi, ShareAlreadyExistsError
from cs3api4lab.auth import RevaPassword
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager


class ExtAuthenticator(RevaPassword):

    def __init__(self, config, log):
        super().__init__(config, log)
        self.config = config
        self.log = log
        channel = ChannelConnector().get_channel()
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(channel)


class ExtCs3File(Cs3FileApi):

    def __init__(self, log, config) -> None:
        self.log = log
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        channel = ChannelConnector().get_channel()
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(channel)


class ExtCs3ShareApi(Cs3ShareApi):

    def __init__(self, log, config) -> None:
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        self.file_api = ExtCs3File(log, config)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(ChannelConnector().get_channel())
        self.log = log

    def list(self):
        list_response = self._list()
        return self._map_given_shares(list_response)


class ExtCS3APIsManager(CS3APIsManager):

    def __init__(self, parent, log, config):
        self.cs3_config = config
        self.log = log
        self.file_api = ExtCs3File(log, config)


class TestCs3ShareApi(TestCase, LoggingConfigurable):
    api = None
    config = None
    share_id = None

    receiver_id = 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c'
    receiver_idp = 'cesnet.cz'

    receiver2_id = '932b4540-8d16-481e-8ef4-588e4b6b151c'
    receiver2_idp = 'example.org'

    receiver3_id = '4c510ada-c86b-4815-8820-42cdf82c3d51'
    receiver3_idp = 'example.org'

    receiver_role = 'viewer'
    receiver_grantee_type = 'user'
    storage_id = '123e4567-e89b-12d3-a456-426655440000'

    viewer_role = 'viewer'
    editor_role = 'editor'

    endpoint = "/"

    container = '/home'
    container_path = '/home/test_share_dir'
    file_path = '/home/test_share_file.txt'
    content = f"Lorem ipsum..."

    container2_path = '/home/test_einstein_share_dir'
    file2_path = '/home/test_einstein_share_file.txt'

    first_client_id = "einstein"
    first_client_secret = "relativity"
    first_file_name = "/home/test_file_einstein.txt"
    share_first_file_name = "/reva/einstein/test_file_einstein.txt"

    second_client_id = "marie"
    second_client_secret = "radioactivity"
    second_file_name = "/home/test_file_marie.txt"

    def setUp(self):
        self.config = Cs3ConfigManager().get_config()
        self.config_ext = self.config.copy()

        self.config["client_id"] = self.first_client_id
        self.config["client_secret"] = self.first_client_secret

        self.config_ext["client_id"] = self.second_client_id
        self.config_ext["client_secret"] = self.second_client_secret

        self.storage = ExtCs3File(self.log, self.config)
        self.api = ExtCs3ShareApi(self.log, self.config)

        self.storage_ext = ExtCs3File(self.log, self.config_ext)
        self.api_ext = ExtCs3ShareApi(self.log, self.config_ext)

        self.manager_ext = ExtCS3APIsManager(None, self.log, self.config_ext)

    def test_read_file_by_share_path(self):

        self._write_test_files()

        file_content = self._read_storage_file(self.first_file_name)
        share_file_content = self._read_storage_file(self.share_first_file_name)

        self._remove_test_files()
        self.assertEqual(file_content, share_file_content)

    def test_share_file_and_read(self):
        self._clear_shares(self.file_path)
        self._remove_test_file()

        self._create_file_share()

        marie_list_received = self.api_ext.list_received()

        file_content = self._read_storage_file(self.file_path)
        marie_file_content = self._read_storage_ext_file(marie_list_received['content'][0]['path'])

        self._clear_shares(self.file_path)
        self._remove_test_file()

        self.assertEqual(file_content, marie_file_content)

    def test_share_container_and_read(self):

        self._clear_shares(self.container_path)
        self._remove_test_container()

        try:
            self._create_container_share()
        except ShareAlreadyExistsError as e:
            print("Error create share:", e)

        marie_list_received = self.api_ext.list_received()

        try:
            marie_stat = self.storage_ext.stat(marie_list_received['content'][0]['path'])
            print("Marie - marie_stat: ", marie_stat)
        except IOError as e:
            print("Error stat marie container:", e)

        try:
            marie_directory = self.storage_ext.read_directory(marie_stat['filepath'])
            print("Marie - marie_directory: ", marie_directory)
        except IOError as e:
            print("Error read marie container:", e)

        marie_file_content = self._read_storage_ext_file(marie_directory[1].path)

        self._clear_shares(self.container_path)
        self._remove_test_container()

        self.assertEqual(marie_file_content, 'Lorem ipsum 111 ...')

    def test_create_folder_in_share_folder(self):

        self._clear_shares(self.container_path)
        self._remove_test_container()

        self._create_container_share()

        marie_list_received = self.api_ext.list_received()
        share_dir = marie_list_received['content'][0]['path']
        self.storage_ext.create_directory(share_dir + "/test_share_subdir")

        directory_list = self.storage_ext.read_directory(share_dir)

        try:
            if not list(filter(lambda s: s.path == "/reva/einstein/test_share_dir/test_share_subdir", directory_list)):
                raise Exception("Subfolder in share folder not created")
        finally:
            self._clear_shares(self.container_path)
            self._remove_test_container()

    def test_create_file_in_share_folder(self):

        self._clear_shares(self.container_path)
        self._remove_test_container()

        self._create_container_share()

        marie_list_received = self.api_ext.list_received()
        share_dir = marie_list_received['content'][0]['path']
        file_path = share_dir + "/test_share.txt"
        self.storage_ext.write_file(file_path, "Lorem ipsum ...")
        share_file_content = self._read_storage_file(file_path)

        self._clear_shares(self.container_path)
        self._remove_test_container()

        self.assertEqual(share_file_content, "Lorem ipsum ...")

    def test_create_empty_file_in_share_folder(self):

        self._clear_shares(self.container_path)
        self._remove_test_container()

        self._create_container_share()

        marie_list_received = self.api_ext.list_received()
        share_dir = marie_list_received['content'][0]['path']
        file_path = share_dir + "/test_empty_share.txt"
        self.storage_ext.write_file(file_path, "")
        share_file_content = self._read_storage_file(file_path)

        self._clear_shares(self.container_path)
        self._remove_test_container()

        self.assertEqual(share_file_content, "")

    def test_read_write_flag_in_share_folder(self):

        share_folder = '/home/test_share_dir/'
        write_folder_id = '/home/test_share_dir/test_write_folder'
        read_folder_id = '/home/test_share_dir/test_read_folder'

        self._create_dir(share_folder)
        self._create_dir(write_folder_id)
        self._create_dir(read_folder_id)

        try:
            self.api.create(self.endpoint,
                            write_folder_id,
                            self.receiver_id,
                            self.receiver_idp,
                            self.editor_role,
                            self.receiver_grantee_type)
        except ShareAlreadyExistsError as e:
            print("Error create share: ", e)

        try:
            self.api.create(self.endpoint,
                            read_folder_id,
                            self.receiver_id,
                            self.receiver_idp,
                            self.viewer_role,
                            self.receiver_grantee_type)
        except ShareAlreadyExistsError as e:
            print("Error create share: ", e)

        marie_list_received = self.api_ext.list_received()
        marie_read_dir = list(filter(lambda s: s['path'] == "/reva/einstein/test_share_dir/test_read_folder", marie_list_received['content']))
        marie_write_dir = list(filter(lambda s: s['path'] == "/reva/einstein/test_share_dir/test_write_folder", marie_list_received['content']))

        self._clear_shares(write_folder_id)
        self._clear_shares(read_folder_id)
        self.storage.remove(share_folder)

        self.assertTrue(marie_write_dir[0]['writable'])
        self.assertFalse(marie_read_dir[0]['writable'])

    def test_create_notebook_file_in_share_folder(self):

        self._clear_shares(self.container_path)
        self._remove_test_container()

        self._create_container_share()

        marie_list_received = self.api_ext.list_received()
        share_dir = marie_list_received['content'][0]['path']
        file_path = share_dir + "/test_share_notebook.ipynb"

        buffer = b'{\
					"cells": [\
						{\
							"cell_type": "markdown",\
							"metadata": {},\
							"source": [\
								"### Markdown example"\
							]\
						}\
					],\
					"metadata": {\
						"kernelspec": {\
							"display_name": "Python 3",\
							"language": "python",\
							"name": "python3"\
						},\
						"language_info": {\
							"codemirror_mode": {\
								"name": "ipython",\
								"version": 3\
							},\
							"file_extension": ".py",\
							"mimetype": "text/x-python",\
							"name": "python",\
							"nbconvert_exporter": "python",\
							"pygments_lexer": "ipython3",\
							"version": "3.7.4"\
						}\
					},\
					"nbformat": 4,\
					"nbformat_minor": 4\
					}'

        self.storage.write_file(file_path, buffer, self.endpoint)

    @skip
    def test_create_share_for_marie(self):
        self._clear_shares(self.container_path)
        self._remove_test_container()
        self._create_file_share()
        self._create_container_share()

    @skip
    def test_create_share_for_einstein(self):

        self.storage_ext.write_file(self.file2_path,
                                    self.content,
                                    self.endpoint)

        try:
            self.api_ext.create(self.endpoint,
                                self.file2_path,
                                self.receiver3_id,
                                self.receiver3_idp,
                                self.receiver_role,
                                self.receiver_grantee_type)
        except ShareAlreadyExistsError as e:
            print("Error create share...", e)

        try:
            self.storage_ext.create_directory(self.container2_path, self.endpoint)
        except IOError as e:
            print("Error create dir...", e)

        self.storage_ext.write_file(self.container2_path + "/test1.txt", "Lorem ipsum 111 ...", self.endpoint)
        self.storage_ext.write_file(self.container2_path + "/test2.txt", "Lorem ipsum 222 ...", self.endpoint)
        self.storage_ext.write_file(self.container2_path + "/test3.txt", "Lorem ipsum 333 ...", self.endpoint)
        self.storage_ext.write_file(self.container2_path + "/test4.txt", "Lorem ipsum 444 ...", self.endpoint)

        try:
            self.api_ext.create(self.endpoint,
                                self.container2_path,
                                self.receiver3_id,
                                self.receiver3_idp,
                                self.receiver_role,
                                self.receiver_grantee_type)
        except ShareAlreadyExistsError as e:
            print("Error create share...", e)

    @skip
    def test_print_list_received_share(self):
        list_received = self.api_ext.list_received()
        print(list_received)

    def _create_file_share(self):
        self._create_test_file()
        return self._create_test_share()

    def _create_test_file(self):
        self.storage.write_file(self.file_path,
                                self.content,
                                self.endpoint)

    def _create_test_share(self, receiver_id='f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c', receiver_idp='cesnet.cz'):
        return self.api.create(self.endpoint,
                               self.file_path,
                               receiver_id,
                               receiver_idp,
                               self.receiver_role,
                               self.receiver_grantee_type)

    def _remove_test_file(self):
        try:
            self.storage.remove(self.file_path,
                                self.endpoint)
        except IOError as e:
            print("Error remove_test file:", e)

    def _create_dir(self, path):
        try:
            self.storage.create_directory(path, self.endpoint)
        except Exception as e:
            print(f"Error create dir: {path}", e)

    def _clear_shares(self, path):
        try:
            shares = self.api.list_grantees_for_file(path)
            for share in shares['shares']:
                self.api.remove(share['opaque_id'])
        except:
            print("Error clear shares.")

    def _create_container_share(self):
        self._create_test_container()
        return self._create_test_container_share()

    def _create_test_container(self):
        try:
            self.storage.create_directory(self.container_path, self.endpoint)
        except:
            print("Error create test dir.")

        self.storage.write_file(self.container_path + "/test1.txt", "Lorem ipsum 111 ...", self.endpoint)
        self.storage.write_file(self.container_path + "/test2.txt", "Lorem ipsum 222 ...", self.endpoint)
        self.storage.write_file(self.container_path + "/test3.txt", "Lorem ipsum 333 ...", self.endpoint)
        self.storage.write_file(self.container_path + "/test4.txt", "Lorem ipsum 444 ...", self.endpoint)

        buffer = b'{\
					"cells": [\
						{\
							"cell_type": "markdown",\
							"metadata": {},\
							"source": [\
								"### Markdown example"\
							]\
						}\
					],\
					"metadata": {\
						"kernelspec": {\
							"display_name": "Python 3",\
							"language": "python",\
							"name": "python3"\
						},\
						"language_info": {\
							"codemirror_mode": {\
								"name": "ipython",\
								"version": 3\
							},\
							"file_extension": ".py",\
							"mimetype": "text/x-python",\
							"name": "python",\
							"nbconvert_exporter": "python",\
							"pygments_lexer": "ipython3",\
							"version": "3.7.4"\
						}\
					},\
					"nbformat": 4,\
					"nbformat_minor": 4\
					}'
        file_id = self.container_path + "/example.ipynb"
        self.storage.write_file(file_id, buffer, self.endpoint)

    def _remove_test_container(self):
        try:
            self.storage.remove(self.container_path, self.endpoint)
        except IOError as e:
            print("Error remove test container:", e)

    def _create_test_container_share(self, receiver_id='f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c', receiver_idp='cesnet.cz'):
        file_path = self.container_path
        return self.api.create(self.endpoint,
                               file_path,
                               receiver_id,
                               receiver_idp,
                               self.receiver_role,
                               self.receiver_grantee_type)

    def _write_test_files(self):
        self.storage.write_file(self.first_file_name, self.content)
        self.storage_ext.write_file(self.second_file_name, self.content)

    def _remove_test_files(self):
        try:
            self.storage.remove(self.first_file_name)
            self.storage_ext.remove(self.second_file_name)
        except IOError as e:
            print("Error remove file:", e)

    def _read_storage_file(self, file_path):
        read = ''
        for chunk in self.storage.read_file(file_path):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            read += chunk.decode('utf-8')

        return read

    def _read_storage_ext_file(self, file_path):
        read = ''
        for chunk in self.storage_ext.read_file(file_path):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            read += chunk.decode('utf-8')

        return read

    def _read_storage_ext_file_by_id(self, file_id):
        read = ''
        opaque_id = urllib.parse.unquote(file_id['opaque_id'])

        for chunk in self.storage_ext.read_file(opaque_id, file_id['storage_id']):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            read += chunk.decode('utf-8')

        return read
