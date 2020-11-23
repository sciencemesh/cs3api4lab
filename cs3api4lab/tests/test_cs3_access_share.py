from unittest import TestCase

import cs3
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
from traitlets.config import LoggingConfigurable

import cs3.app.provider.v1beta1.provider_api_pb2_grpc as provider_api_pb2_grpc


from cs3api4lab.api.file_utils import FileUtils as file_utils
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.auth.authenticator import Authenticator
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager


class ExtAuthenticator(Authenticator):

    def __init__(self, config):
        self.config = config
        channel = ChannelConnector().channel
        self.cs3_stub = cs3gw_grpc.GatewayAPIStub(channel)


class ExtCs3File(Cs3FileApi):

    def __init__(self, log, config) -> None:
        self.log = log
        self.config = config
        self.auth = ExtAuthenticator(config)
        channel = ChannelConnector().channel
        self.cs3_stub = cs3gw_grpc.GatewayAPIStub(channel)


class ExtCs3ShareApi(Cs3ShareApi):

    def __init__(self, log, config) -> None:
        self.config = config
        self.auth = ExtAuthenticator(config)
        self.file_api = ExtCs3File(log, config)
        self.gateway_stub = cs3gw_grpc.GatewayAPIStub(ChannelConnector().channel)
        self.log = log


class TestCs3ShareApi(TestCase, LoggingConfigurable):
    api = None
    config = None
    share_id = None

    receiver_role = 'viewer'
    receiver_grantee_type = 'user'

    storage_id = '123e4567-e89b-12d3-a456-426655440000'
    file_path = '/test.txt'
    container_path = '/test_share_dir'

    second_client_id = "marie"
    second_client_secret = "radioactivity"

    def setUp(self):
        self.config = Cs3ConfigManager().config

        self.client_id = self.config['client_id']
        self.endpoint = self.config['endpoint']

        self.storage = Cs3FileApi(self.log)
        self.api = Cs3ShareApi(self.log)
        self.config_ext = Cs3ConfigManager().config

        self.config_ext["client_id"] = self.second_client_id
        self.config_ext["client_secret"] = self.second_client_secret
        self.storage_ext = ExtCs3File(self.log, self.config_ext)
        self.api_ext = ExtCs3ShareApi(self.log, self.config_ext)

    def test_stat_file_id(self):
        einstein_dir = self.storage.read_directory('/', self.client_id)
        einstein_stat = self.storage.stat(einstein_dir[0].id.opaque_id, self.client_id, einstein_dir[0].id.storage_id)
        print("einstein_stat: ", einstein_stat)

        marie_dir = self.storage_ext.read_directory('/', self.second_client_id)
        marie_stat = self.storage_ext.stat(marie_dir[0].id.opaque_id, self.second_client_id, marie_dir[0].id.storage_id)
        print("marie_dir[0]: ", marie_dir[0])
        print("marie_stat: ", marie_stat)

        marie_read = ''
        for chunk in self.storage_ext.read_file(marie_dir[0].id.opaque_id, self.second_client_id, marie_dir[0].id.storage_id):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            print("chunk: ", chunk)
            marie_read += chunk.decode('utf-8')

        print("marie_read: ", marie_read)

    def test_create_directory_and_list(self):
        try:
            self._remove_test_container()
            self._clear_shares()

        except IOError as e:
            print("Error remove file:", e)

        created_share = self._create_container_share()
        share_list = self.api.list()
        list_received = self.api.list_received()

        print("Einstein - created_share: ", created_share)
        print("Einstein - share_list: ", share_list)
        print("Einstein - list_received: ", list_received)

        ext_list_received = self.api_ext.list_received()
        print("Marie - list_received: ", ext_list_received)

        self.assertEqual(ext_list_received[0]['id']['opaque_id'], 'fileid-einstein/test_share_dir')
        self.assertEqual(ext_list_received[0]['id']['storage_id'], '123e4567-e89b-12d3-a456-426655440000')

        reference = file_utils.get_reference(ext_list_received[0]['id']['opaque_id'], self.config['home_dir'], ext_list_received[0]['id']['storage_id'])


        # cs3.app.provider.v1beta1.OpenFileInAppProviderRequest()
        # cs3.app.provider.v1beta1.provider_api_pb2_grpc.OpenFileInAppProviderRequest()
        # cs3.app.provider.v1beta1.OpenFileInAppProviderRequest
        # cs3.gateway.v1beta1.gateway_api_pb2_grpc.OpenFileInAppProvider

        # cs3.app.provider.v1beta1.provider_api_pb2_grpc.OpenFileInAppProviderRequest

        # req = cs3.app.providerprovider_api_pb2.OpenFileInAppProviderRequest(ref=reference)
        # res = self.api_ext.gateway_stub.OpenFileInAppProvider(request=req, metadata=[('x-access-token', self.api_ext.get_token())])
        # print(res)

        # stat = self.storage_ext.stat(ext_list_received[0]['id']['opaque_id'], s
        # lf.second_client_id, ext_list_received[0]['id']['storage_id'])
        # print(stat)

    def _create_share(self):
        self._create_test_container()
        return self._create_test_container_share()

    def _clear_shares(self):
        shares = self.api.list()
        for share in shares:
            self._remove_test_share(share['opaque_id'])
        try:
            self._remove_test_file()
        except IOError as e:
            print("Error remove file:", e)

    def _create_test_share(self, receiver_id='f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c', receiver_idp='cesnet.cz'):
        file_path = self.config['home_dir'] + self.file_path
        return self.api.create(self.config['endpoint'],
                               file_path,
                               receiver_id,
                               receiver_idp,
                               self.receiver_role,
                               self.receiver_grantee_type)

    def _remove_test_share(self, share_id):
        self.api.remove(share_id)

    def _create_test_file(self):
        self.storage.write_file(self.file_path,
                                self.config['client_id'],
                                "Lorem ipsum dolor sit amet...",
                                self.config['endpoint'])

    def _remove_test_file(self):
        self.storage.remove(self.file_path,
                            self.config['client_id'],
                            self.config['endpoint'])

    def _create_container_share(self):
        self._create_test_container()
        return self._create_test_container_share()

    def _create_test_container(self):
        self.storage.create_directory(self.container_path, self.config['client_id'], self.config['endpoint'])
        self.storage.write_file(self.container_path + "/test1.txt", self.config['client_id'], "Lorem ipsum 111 ...", self.config['endpoint'])
        self.storage.write_file(self.container_path + "/test2.txt", self.config['client_id'], "Lorem ipsum 222 ...", self.config['endpoint'])
        self.storage.write_file(self.container_path + "/test3.txt", self.config['client_id'], "Lorem ipsum 333 ...", self.config['endpoint'])
        self.storage.write_file(self.container_path + "/test4.txt", self.config['client_id'], "Lorem ipsum 444 ...", self.config['endpoint'])

    def _remove_test_container(self):
        self.storage.remove(self.container_path, self.config['client_id'], self.config['endpoint'])

    def _create_test_container_share(self, receiver_id='f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c', receiver_idp='cesnet.cz'):
        file_path = self.config['home_dir'] + self.container_path
        return self.api.create(self.config['endpoint'],
                               file_path,
                               receiver_id,
                               receiver_idp,
                               self.receiver_role,
                               self.receiver_grantee_type)
