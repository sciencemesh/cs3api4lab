from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi
from cs3api4lab.api.share_api_facade import ShareAPIFacade

from cs3api4lab.auth.authenticator import Auth
import cs3.ocm.provider.v1beta1.provider_api_pb2_grpc as ocm_provider_api_grpc

import random
import string
from unittest import TestCase
from traitlets.config import LoggingConfigurable
from cs3api4lab.api.cs3_user_api import Cs3UserApi
from cs3api4lab import CS3APIsManager
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.auth import RevaPassword
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager

import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.identity.user.v1beta1.user_api_pb2_grpc as user_api_grpc
import cs3.sharing.ocm.v1beta1.ocm_api_pb2_grpc as ocm_api_grpc
import grpc

from cs3api4lab.auth import check_auth_interceptor
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway


class ExtCs3ConfigManager(Cs3ConfigManager):
    def __init__(self, config, log):
        super().__init__(config, log)
        self.config = config
        self.log = log


class ExtAuthenticator(RevaPassword):
    def __init__(self, config, log):
        super().__init__(config, log)
        self.config = config
        self.log = log
        channel = grpc.insecure_channel(config['reva_host'])
        self.cs3_stub = cs3gw_grpc.GatewayAPIStub(channel)


class ExtCs3FileApi(Cs3FileApi):
    def __init__(self, log, config) -> None:
        # super().__init__(config, log)
        self.log = log
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        channel = grpc.insecure_channel(config['reva_host'])
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)


class ExtCs3ShareApi(Cs3ShareApi):
    def __init__(self, log, config) -> None:
        # super().__init__(config, log)
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        self.file_api = ExtCs3FileApi(log, config)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(ChannelConnector().get_channel())
        self.log = log

    def list(self):
        list_response = self.list()
        return self._map_given_shares(list_response)


class ExtUserApi(Cs3UserApi):
    def __init__(self, log, config) -> None:
        # super().__init__(config, log)
        self.api = user_api_grpc.UserAPIStub(ChannelConnector().get_channel())
        self.config = config
        self.auth = ExtAuthenticator(config, log)


class ExtCS3APIsManager(CS3APIsManager):
    def __init__(self, parent, log, config):
        super().__init__(config, log)
        self.cs3_config = config
        self.log = log
        self.file_api = ExtCs3FileApi(log, config)


class ExtCs3OcmShareApi(Cs3OcmShareApi):
    def __init__(self, log, config) -> None:
        # super().__init__(config, log)
        self.log = log
        self.config = config
        channel = grpc.insecure_channel(config['reva_host'])
        self.auth = ExtAuthenticator(config, log)
        self.auth.cs3_stub = cs3gw_grpc.GatewayAPIStub(channel)
        self.file_api = Cs3FileApi(log)
        channel = grpc.insecure_channel(config['reva_host'])
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = grpc_gateway.GatewayAPIStub(intercept_channel)
        self.ocm_share_api = ocm_api_grpc.OcmAPIStub(channel)
        self.provider_api = ocm_provider_api_grpc.ProviderAPIStub(channel)


class ExtCs3ShareApiFacade(ShareAPIFacade):

    def __init__(self, log, config) -> None:
        # super().__init__(config, log)
        self.log = log
        self.config = config
        self.auth = Auth.get_authenticator(config=config, log=self.log)
        self.file_api = ExtCs3FileApi(log, config)

        channel = ChannelConnector().get_channel()
        self.provider_api = ocm_provider_api_grpc.ProviderAPIStub(channel)
        self.user_api = ExtUserApi(log, config)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(ChannelConnector().get_channel())

        self.share_api = ExtCs3ShareApi(log, config)
        self.ocm_share_api = ExtCs3OcmShareApi(log, config)


class TestCs3UniShareApi(TestCase, LoggingConfigurable):
    einstein_id = '4c510ada-c86b-4815-8820-42cdf82c3d51'
    einstein_idp = 'cernbox.cern.ch'
    marie_id = 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c'
    marie_idp = 'cesnet.cz'
    richard_id = '932b4540-8d16-481e-8ef4-588e4b6b151c'
    richard_idp = 'example.org'
    receiver_role = 'viewer'
    receiver_grantee_type = 'user'
    file_path = '/home/test.txt'
    storage_id = '123e4567-e89b-12d3-a456-426655440000'

    def setUp(self):
        self.file_api = Cs3FileApi(self.log)
        self.share_api = Cs3ShareApi(self.log)
        self.ocm_api = Cs3OcmShareApi(self.log)
        self.uni_api = ShareAPIFacade(self.log)

        marie_ext_config = {
            "reva_host": "127.0.0.1:29000",
            "auth_token_validity": "3600",
            "endpoint": "/",
            "home_dir": "/home",
            "chunk_size": "4194304",
            "secure_channel": False,
            "client_cert": "",
            "client_key": "",
            "ca_cert": "",
            "authenticator_class": "cs3api4lab.auth.RevaPassword",
            "client_id": "marie",
            "client_secret": "radioactivity"
            }
        richard_local_config = {
            "reva_host": "127.0.0.1:19000",
            "auth_token_validity": "3600",
            "endpoint": "/",
            "home_dir": "/home",
            "chunk_size": "4194304",
            "secure_channel": False,
            "client_cert": "",
            "client_key": "",
            "ca_cert": "",
            "authenticator_class": "cs3api4lab.auth.RevaPassword",
            "client_id": "richard",
            "client_secret": "superfluidity"
        }
        self.marie_uni_api = ExtCs3ShareApiFacade(self.log, marie_ext_config)
        self.marie_file_api = ExtCs3FileApi(self.log, marie_ext_config)
        self.marie_share_api = ExtCs3ShareApi(self.log, marie_ext_config)
        self.marie_ocm_share_api = ExtCs3OcmShareApi(self.log, marie_ext_config)

        self.richard_uni_api = ExtCs3ShareApiFacade(self.log, richard_local_config)
        self.richard_file_api = ExtCs3FileApi(self.log, richard_local_config)
        self.richard_share_api = ExtCs3ShareApi(self.log, richard_local_config)
        self.richard_ocm_share_api = ExtCs3OcmShareApi(self.log, richard_local_config)

    def test_create(self):
        try:
            self.file_name = self.file_path + self._get_file_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.ocm_file_name = self.file_path + self._get_file_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']
            share_list = self.uni_api.list_shares()
            contains = False
            contains_ocm = False
            for share in share_list['content']:
                if share['path'].__contains__(self.file_name.split('/')[-1]):
                    contains = True
                if share['path'].__contains__(self.ocm_file_name.split('/')[-1]):
                    contains_ocm = True
            if not (contains and contains_ocm):
                raise Exception("Shares not present")
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_list_received(self):
        try:
            self.file_name = self.file_path + self._get_file_suffix()
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.ocm_file_name = self.file_path + self._get_file_suffix()
            created_ocm_share = self.create_ocm_share('marie', self.einstein_id, self.einstein_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']
            share_list = self.uni_api.list_received()
            contains = False
            contains_ocm = False
            for share in share_list['content']:
                if share['path'].__contains__(self.file_name.split('/')[-1]):
                    contains = True
                if share['path'].__contains__(self.ocm_file_name.split('/')[-1]):
                    contains_ocm = True
            if not (contains and contains_ocm):
                raise Exception("Shares not present")
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('marie', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('marie', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_update_received(self):
        try:
            self.file_name = self.file_path + self._get_file_suffix()
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.ocm_file_name = self.file_path + self._get_file_suffix()
            created_ocm_share = self.create_ocm_share('marie', self.einstein_id, self.einstein_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']

            self.uni_api.update_received(self.share_id, 'ACCEPTED')
            received_file_path = '/home/MyShares/' + self.file_name.split('/')[-1]
            file_stat = self.file_api.stat(received_file_path, self.storage_id)
            if file_stat['filepath'] != received_file_path:
                raise Exception('Share not updated')

            for share in self.ocm_api.list_received().shares:
                if share.share.resource_id.opaque_id == self.ocm_file_name:
                    ocm_share_id = share.share.id.opaque_id
            if ocm_share_id is None:
                raise Exception('OCM Received share not found')

            # self.uni_api.update_received(ocm_share_id, 'ACCEPTED')
            # received_ocm_file_path = '/home/MyShares/' + self.ocm_file_name.split('/')[-1]
            # ocm_file_stat = self.file_api.stat(received_ocm_file_path, self.storage_id)
            # if ocm_file_stat['filepath'] != received_ocm_file_path:
            #     raise Exception('OCM Share not updated')
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('marie', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('marie', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_remove(self):
        try:
            self.file_name = self.file_path + self._get_file_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.ocm_file_name = self.file_path + self._get_file_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']

            share_list = self.uni_api.list_shares()
            contains = False
            contains_ocm = False
            for share in share_list['content']:
                if share['path'].__contains__(self.file_name.split('/')[-1]):
                    contains = True
                if share['path'].__contains__(self.ocm_file_name.split('/')[-1]):
                    contains_ocm = True
            if not (contains and contains_ocm):
                raise Exception("Shares not present")

            self.uni_api.remove(self.share_id)
            self.uni_api.remove(self.ocm_share_id)

            share_list = self.uni_api.list_shares()
            contains = False
            contains_ocm = False
            for share in share_list['content']:
                if share['path'].__contains__(self.file_name.split('/')[-1]):
                    contains = True
                if share['path'].__contains__(self.ocm_file_name.split('/')[-1]):
                    contains_ocm = True
            if contains or contains_ocm:
                raise Exception("Shares not removed")
        finally:
            if contains:
                self.remove_test_share('einstein', self.share_id)
            if contains_ocm:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_get_grantees_for_file(self):
        try:
            self.file_name = self.file_path + self._get_file_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.ocm_file_name = self.file_path + self._get_file_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']

            grantees = self.uni_api.list_grantees_for_file(self.file_name)
            if not grantees['shares']:
                raise Exception("Grantees not found")

            grantees = self.uni_api.list_grantees_for_file(self.ocm_file_name)
            if not grantees['shares']:
                raise Exception("Grantees not found")

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def create_ocm_share(self, user, ocm_receiver_id, ocm_receiver_idp, file_path):
        self.create_test_file(user, file_path)
        if user == 'einstein':
            return self.ocm_api.create(ocm_receiver_id,
                                       ocm_receiver_idp,
                                       ocm_receiver_idp,
                                       self.storage_id, file_path)
        if user == 'marie':
            return self.marie_ocm_share_api.create(ocm_receiver_id,
                                                   ocm_receiver_idp,
                                                   ocm_receiver_idp,
                                                   self.storage_id, file_path)
        if user == 'richard':
            return self.richard_ocm_share_api.create(ocm_receiver_id,
                                                     ocm_receiver_idp,
                                                     ocm_receiver_idp,
                                                     self.storage_id, file_path)

    def create_share(self, user, receiver_id, receiver_idp, file_path):
        self.create_test_file(user, file_path)
        if user == 'einstein':
            return self.share_api.create(self.storage_id,
                                         file_path,
                                         receiver_id,
                                         receiver_idp,
                                         self.receiver_role,
                                         self.receiver_grantee_type)
        if user == 'marie':
            return self.marie_share_api.create(self.storage_id,
                                               file_path,
                                               receiver_id,
                                               receiver_idp,
                                               self.receiver_role,
                                               self.receiver_grantee_type)
        if user == 'richard':
            return self.richard_share_api.create(self.storage_id,
                                                 file_path,
                                                 receiver_id,
                                                 receiver_idp,
                                                 self.receiver_role,
                                                 self.receiver_grantee_type)

    def remove_test_share(self, user, share_id):
        if user == 'einstein':
            self.share_api.remove(share_id)
        if user == 'marie':
            self.marie_share_api.remove(share_id)
        if user == 'richard':
            self.richard_share_api.remove(share_id)

    def remove_test_ocm_share(self, user, share_id):
        if user == 'einstein':
            self.ocm_api.remove(share_id)
        if user == 'marie':
            self.marie_ocm_share_api.remove(share_id)
        if user == 'richard':
            self.richard_ocm_share_api.remove(share_id)

    def create_test_file(self, user, file_path):
        if user == 'einstein':
            self.file_api.write_file(file_path,
                                     "Lorem ipsum dolor sit amet...",
                                     self.storage_id)
        if user == 'marie':
            self.marie_file_api.write_file(file_path,
                                           "Lorem ipsum dolor sit amet...",
                                           self.storage_id)
        if user == 'richard':
            self.richard_file_api.write_file(file_path,
                                             "Lorem ipsum dolor sit amet...",
                                             self.storage_id)

    def remove_test_file(self, user, file_path):
        if user == 'einstein':
            self.file_api.remove(file_path, self.storage_id)
        if user == 'marie':
            self.marie_file_api.remove(file_path, self.storage_id)
        if user == 'richard':
            self.richard_file_api.remove(file_path, self.storage_id)

    def _get_file_suffix(self):
        return '-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))