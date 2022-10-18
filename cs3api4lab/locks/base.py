from abc import ABC, abstractmethod
import grpc
import datetime
import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.v1beta1.code_pb2 as cs3code

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.api.storage_api import StorageApi


class LockBase(ABC):

    def __init__(self, log, config):
        self.user = None
        self.config = config
        self.auth = Auth.get_authenticator(config=config, log=log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        self.storage_api = StorageApi(log)
        self.lock_name = 'cs3apis4lab_lock'

    @abstractmethod
    def handle_locks(self, file_path, endpoint):
        pass

    def get_current_user(self):
        if self.user is None:
            self.user = self.cs3_api.WhoAmI(request=cs3gw.WhoAmIRequest(token=self.auth.authenticate()),
                                   metadata=[('x-access-token', self.auth.authenticate())])
        return self.user.user

    def resolve_file_path(self, file_path, endpoint):
        if self.is_valid_external_lock(file_path, endpoint):
            file_name = file_path.split('/')[-1]
            file_dir = '/'.join(file_path.split('/')[0:-1])
            return self._resolve_directory(file_dir, endpoint) + self._get_conflict_filename(file_name)
        return file_path

    @abstractmethod
    def is_valid_external_lock(self, file_path, endpoint):
        pass

    def _resolve_directory(self, dir_path,
                           endpoint):  # right now its possible to write in somone else's directory without it being shared
        stat = self.storage_api.stat(dir_path, endpoint)
        if stat.status.code == cs3code.CODE_OK:
            return dir_path
        else:
            return self.config.mount_dir + '/'

    def _get_conflict_filename(self, file_name):
        file_extension = file_name.split('.')[-1]
        name = '.'.join(file_name.split('.')[0:-1])
        return name + '-' + self.get_current_user().username + '.' + datetime.datetime.now().strftime(
            "%Y-%m-%d_%H_%M_%S") + '-conflict.' + file_extension

