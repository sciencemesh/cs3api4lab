import json
import time
import datetime
import grpc

import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.logic.storage_logic import StorageLogic
from cs3api4lab.api.cs3_user_api import Cs3UserApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.exception.exceptions import LockNotFoundError

class LockManager:

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)

        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)

        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        self.user_api = Cs3UserApi(log)
        self.storage_logic = StorageLogic(log)
        self.locks_expiration_time = self.config['locks_expiration_time']

    def generate_lock_entry(self):
        user = self._get_current_user()
        return {self.get_my_lock_name(): json.dumps({
            "username": user.username,
            "idp": user.id.idp,
            "opaque_id": user.id.opaque_id,
            "updated": time.time(),
            "created": time.time()
        })}

    def get_my_lock_name(self):
        user = self._get_current_user()
        return 'lock_' + user.username + '_' + user.id.idp + '_' + user.id.opaque_id

    def get_lock_path(self, file_path):
        file_name = '.' + file_path.split('/')[-1] + '.lock'
        return self.config['home_dir'] + '/' + file_name

    def lock_file(self, file_path, endpoint):
        self.storage_logic.set_metadata(self.generate_lock_entry(), file_path, endpoint)

    def is_lock_mine(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)
        user = self._get_current_user()
        if lock:
            return lock['username'] == user.username #todo add more checks, ie idp
        return False        

    def is_lock_expired(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)
        if not lock:
            return True
        return time.time() - lock['updated'] > datetime.timedelta(seconds=self.locks_expiration_time).total_seconds()

    def is_file_locked(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)
        return True if lock else False

    def handle_locks_write(self, file_path, endpoint):
        is_locked = self.is_file_locked(file_path, endpoint)
        is_mine = self.is_lock_mine(file_path, endpoint)

        if is_locked and not is_mine and not self.is_lock_expired(file_path, endpoint):
            file_name = file_path.split('/')[-1]
            return (self.config['home_dir'] + '/' + file_name + '.conflict')

        return file_path

    def handle_locks_read(self, file_path, endpoint):
        if not self.is_file_locked(file_path, endpoint):
            self.lock_file(file_path, endpoint)
        else:
            if self.is_lock_mine(file_path, endpoint):
                self.lock_file(file_path, endpoint)
            if self.is_lock_expired(file_path, endpoint):
                self.lock_file(file_path, endpoint)
        return

    def get_lock(self, file_path):
        lock = self._get_lock(file_path, None) #todo: test endpoint
        if not lock:
            raise LockNotFoundError("Lock not found for file: " + file_path)
        if self.is_lock_mine(file_path, None):
            raise LockNotFoundError("Lock belongs to the user")
        if self.is_lock_expired(file_path, None):
            raise LockNotFoundError("Lock is expired")
        return lock

    def _get_current_user(self):
        user = self.cs3_api.WhoAmI(request=cs3gw.WhoAmIRequest(token=self.auth.authenticate()),
                                   metadata=self._get_token())
        return user.user

    def _get_token(self):
        return [('x-access-token', self.auth.authenticate())]

    def _get_lock(self, file_path, endpoint):
        metadata = self.storage_logic.get_metadata(file_path, endpoint)
        if not metadata:
            return
        return json.loads(list(metadata.values())[0])