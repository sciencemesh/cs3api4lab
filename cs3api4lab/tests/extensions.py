import grpc

from cs3api4lab.api.lock_manager import LockManager
from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi
from cs3api4lab.api.share_api_facade import ShareAPIFacade

from cs3api4lab.auth.authenticator import Auth

from cs3api4lab.api.cs3_user_api import Cs3UserApi
from cs3api4lab import CS3APIsManager
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.auth import RevaPassword
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.logic.storage_logic import StorageLogic

import cs3.ocm.provider.v1beta1.provider_api_pb2_grpc as ocm_provider_api_grpc
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.identity.user.v1beta1.user_api_pb2_grpc as user_api_grpc
import cs3.sharing.ocm.v1beta1.ocm_api_pb2_grpc as ocm_api_grpc
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway

class ExtStorageLogic(StorageLogic):
    def __init__(self, log, config, channel):
        #super().__init__(log)
        self.log = log
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(channel)

class ExtLockManager(LockManager):
    def __init__(self, log, config, channel):
        #super().__init__(log)
        self.config = config
        self.log = log
        self.auth = ExtAuthenticator(config, log)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(channel)
        self.user_api = ExtUserApi(log, config)
        self.storage_logic = ExtStorageLogic(log, config, channel)
        self.locks_expiration_time = config['locks_expiration_time']

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
        self.lock_manager = ExtLockManager(log, config, intercept_channel)
        self.storage_logic = ExtStorageLogic(log, config, channel)


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