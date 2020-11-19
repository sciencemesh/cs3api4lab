import urllib.parse
from unittest import TestCase

import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
from traitlets.config import LoggingConfigurable

from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.auth.authenticator import Authenticator
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager


class ExtAuthenticator(Authenticator):

    def __init__(self, config):
        self.config = config
        channel = ChannelConnector().get_channel()
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(channel)


class ExtCs3File(Cs3FileApi):

    def __init__(self, log, config) -> None:
        self.log = log
        self.config = config
        self.auth = ExtAuthenticator(config)
        channel = ChannelConnector().get_channel()
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(channel)


class ExtCs3ShareApi(Cs3ShareApi):

    def __init__(self, log, config) -> None:
        self.config = config
        self.auth = ExtAuthenticator(config)
        self.file_api = ExtCs3File(log, config)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(ChannelConnector().get_channel())
        self.log = log

    def list(self):
        list_response = self._list()
        return self._map_given_shares(list_response)


class TestCs3ShareApi(TestCase, LoggingConfigurable):
    api = None
    config = None
    share_id = None

    receiver_id = 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c'
    receiver_idp = 'cesnet.cz'

    receiver2_id = '932b4540-8d16-481e-8ef4-588e4b6b151c'
    receiver2_idp = 'example.org'

    receiver_role = 'viewer'
    receiver_grantee_type = 'user'
    storage_id = '123e4567-e89b-12d3-a456-426655440000'

    endpoint = "/"

    container_path = '/test_share_dir'
    file_path = '/test_share_file.txt'
    content = f"Lorem ipsum..."

    first_client_id = "einstein"
    first_client_secret = "relativity"
    first_file_name = "/test_file_einstein.txt"

    second_client_id = "marie"
    second_client_secret = "radioactivity"
    second_file_name = "/test_file_marie.txt"

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

    def test_read_file_by_id(self):

        self._write_test_files()

        einstein_dir = self.storage.read_directory('/', self.first_client_id, self.endpoint)
        einstein_stat = self.storage.stat(einstein_dir[0].id.opaque_id, self.first_client_id, einstein_dir[0].id.storage_id)

        marie_dir = self.storage_ext.read_directory('/', self.second_client_id, self.endpoint)
        marie_stat = self.storage_ext.stat(marie_dir[0].id.opaque_id, self.second_client_id, marie_dir[0].id.storage_id)

        marie_read = self._read_storage_ext_file(self.second_file_name, self.second_client_id)
        marie_read_by_id = self._read_storage_ext_file_by_id(marie_stat['inode'], self.second_client_id)

        self._remove_test_files()

        self.assertEqual(einstein_stat['inode']['storage_id'], '123e4567-e89b-12d3-a456-426655440000')
        self.assertEqual(einstein_stat['inode']['opaque_id'], 'fileid-einstein%2Ftest_file_einstein.txt')

        self.assertEqual(marie_stat['inode']['storage_id'], '123e4567-e89b-12d3-a456-426655440000')
        self.assertEqual(marie_stat['inode']['opaque_id'], 'fileid-marie%2Ftest_file_marie.txt')

        self.assertEqual(marie_read, marie_read_by_id)

    def test_share_container_and_read(self):

        created_share = self._create_container_share()
        share_list = self.api.list()
        list_received = self.api.list_received()

        print("Einstein - created_share: ", created_share)
        print("Einstein - share_list: ", share_list)
        print("Einstein - list_received: ", list_received)

        marie_list_received = self.api_ext.list_received()
        print("Marie - list_received: ", marie_list_received)

        try:
            marie_stat = self.storage_ext.stat(marie_list_received[0]['id']['opaque_id'], self.second_client_id, marie_list_received[0]['id']['storage_id'])
            print("Marie - marie_stat: ", marie_stat)
        except IOError as e:
            print("Error stat marie container:", e)

        try:
            marie_directory = self.storage_ext.read_directory(marie_list_received[0]['id']['opaque_id'], self.second_client_id,
                                                              marie_list_received[0]['id']['storage_id'])
            print("Marie - marie_directory: ", marie_directory)
        except IOError as e:
            print("Error read marie container:", e)

        self._clear_shares(self.container_path)
        self._remove_test_container()

        self.assertEqual(marie_list_received[0]['id']['opaque_id'], 'fileid-einstein/test_share_dir')
        self.assertEqual(marie_list_received[0]['id']['storage_id'], '123e4567-e89b-12d3-a456-426655440000')

    def test_share_file_and_read(self):
        self._clear_shares(self.file_path)
        self._remove_test_file()

        created_share = self._create_file_share()
        share_list = self.api.list()
        list_received = self.api.list_received()

        print("Einstein - created_share: ", created_share)
        print("Einstein - share_list: ", share_list)
        print("Einstein - list_received: ", list_received)

        marie_list_received = self.api_ext.list_received()
        print("Marie - list_received: ", marie_list_received)

        try:
            marie_stat = self.storage_ext.stat(marie_list_received[0]['id']['opaque_id'], self.second_client_id, marie_list_received[0]['id']['storage_id'])
            print("Marie - marie_stat: ", marie_stat)
        except IOError as e:
            print("Error stat marie file:", e)

        try:
            read_file = self._read_storage_ext_file_by_id(marie_list_received[0]['id'], self.second_client_id)
            print(read_file)
        except IOError as e:
            print("Error read file marie:", e)

        self._clear_shares(self.file_path)
        self._remove_test_file()

        self.assertEqual(marie_list_received[0]['id']['opaque_id'], 'fileid-einstein/test_share_file.txt')
        self.assertEqual(marie_list_received[0]['id']['storage_id'], '123e4567-e89b-12d3-a456-426655440000')

    def _create_file_share(self):
        self._create_test_file()
        return self._create_test_share()

    def _create_test_file(self):
        self.storage.write_file(self.file_path,
                                self.first_client_id,
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
                                self.first_client_id,
                                self.endpoint)
        except IOError as e:
            print("Error remove_test file:", e)

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
        self.storage.create_directory(self.container_path, self.first_client_id, self.endpoint)
        self.storage.write_file(self.container_path + "/test1.txt", self.first_client_id, "Lorem ipsum 111 ...", self.endpoint)
        self.storage.write_file(self.container_path + "/test2.txt", self.first_client_id, "Lorem ipsum 222 ...", self.endpoint)
        self.storage.write_file(self.container_path + "/test3.txt", self.first_client_id, "Lorem ipsum 333 ...", self.endpoint)
        self.storage.write_file(self.container_path + "/test4.txt", self.first_client_id, "Lorem ipsum 444 ...", self.endpoint)

    def _remove_test_container(self):
        try:
            self.storage.remove(self.container_path, self.first_client_id, self.endpoint)
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
        self.storage.write_file(self.first_file_name, self.first_client_id, self.content)
        self.storage_ext.write_file(self.second_file_name, self.second_client_id, self.content)

    def _remove_test_files(self):
        try:
            self.storage.remove(self.first_file_name, self.first_client_id)
            self.storage_ext.remove(self.second_file_name, self.second_client_id)
        except IOError as e:
            print("Error remove file:", e)

    def _read_storage_ext_file(self, file_path, client_id):
        read = ''
        for chunk in self.storage_ext.read_file(file_path, client_id):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            read += chunk.decode('utf-8')

        return read

    def _read_storage_ext_file_by_id(self, file_id, client_id):
        read = ''
        opaque_id = urllib.parse.unquote(file_id['opaque_id'])

        for chunk in self.storage_ext.read_file(opaque_id, client_id, file_id['storage_id']):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            read += chunk.decode('utf-8')

        return read
