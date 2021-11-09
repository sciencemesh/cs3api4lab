import json
<<<<<<< HEAD
import re
=======
>>>>>>> c3f5ea6 (Locking for shares part 1 #11)
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
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 8e0a78a (correct method names in model_utils)
from cs3api4lab.exception.exceptions import LockNotFoundError

class LockManager:
    user = None
<<<<<<< HEAD
=======

class LockManager:
>>>>>>> c3f5ea6 (Locking for shares part 1 #11)
=======
>>>>>>> 185a219 (*WIP* minor fixes)

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

<<<<<<< HEAD
<<<<<<< HEAD
    def _lock_file(self, file_path, endpoint):
        self.storage_logic.set_metadata(self.generate_lock_entry(), file_path, endpoint)

    def is_lock_mine(self, lock):
        user = self._get_current_user()
        if lock:
            return lock['username'] == user.username and lock['idp'] == user.id.idp and lock['opaque_id'] == user.id.opaque_id
        return False        

    def is_lock_expired(self, lock):
=======
    def get_lock_path(self, file_path):
        file_name = '.' + file_path.split('/')[-1] + '.lock'
        return self.config['home_dir'] + '/' + file_name

=======
>>>>>>> 185a219 (*WIP* minor fixes)
    def lock_file(self, file_path, endpoint):
        self.storage_logic.set_metadata(self.generate_lock_entry(), file_path, endpoint)

    def is_lock_mine(self, lock):
        user = self._get_current_user()
        if lock:
            return lock['username'] == user.username and lock['idp'] == user.id.idp and lock['opaque_id'] == user.id.opaque_id
        return False        

<<<<<<< HEAD
    def is_lock_expired(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)
>>>>>>> c3f5ea6 (Locking for shares part 1 #11)
=======
    def is_lock_expired(self, lock):
>>>>>>> 185a219 (*WIP* minor fixes)
        if not lock:
            return True
        return time.time() - lock['updated'] > datetime.timedelta(seconds=self.locks_expiration_time).total_seconds()

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
    def resolve_file_path(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)

        is_locked = True if lock else False
        is_mine = self.is_lock_mine(lock)

        if is_locked and not is_mine and not self.is_lock_expired(lock):
            file_name = file_path.split('/')[-1]
            file_dir = file_path.replace(file_name, '')
            return self._resolve_directory(file_dir, endpoint) + self._get_conflict_filename(file_name)

        return file_path

    def _resolve_directory(self, dir_path, endpoint):#right now its possible to write in somone else's directory without it being shared
        try:
            self.storage_logic.stat(dir_path, endpoint)
            return dir_path
        except:
            return self.config['home_dir'] + '/'

    def _get_conflict_filename(self, file_name):
        return file_name + '.' + self._get_current_user().username + '.' + datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + '.conflict'

    def handle_locks(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)

        if not lock:
            self._lock_file(file_path, endpoint)
            return
        else:
            if self.is_lock_mine(lock):
                self._lock_file(file_path, endpoint)
                return
            if self.is_lock_expired(lock):
                self._lock_file(file_path, endpoint)
                return
        raise IOError("File locked")

    def _get_current_user(self):
        if self.user == None:
            self.user = self.cs3_api.WhoAmI(request=cs3gw.WhoAmIRequest(token=self.auth.authenticate()),
                                   metadata=[('x-access-token', self.auth.authenticate())])
        return self.user.user
=======
    def is_file_locked(self, file_path, endpoint):
=======
    def handle_locks_write(self, file_path, endpoint):
>>>>>>> 185a219 (*WIP* minor fixes)
=======
    def resolve_file_path(self, file_path, endpoint):
>>>>>>> cf96e2d (changes for .conflict files)
        lock = self._get_lock(file_path, endpoint)

        is_locked = True if lock else False
        is_mine = self.is_lock_mine(lock)

        if is_locked and not is_mine and not self.is_lock_expired(lock):
            file_name = file_path.split('/')[-1]
            file_dir = file_path.replace(file_name, '')
            return self._resolve_directory(file_dir, endpoint) + self._resolve_filename(file_name)

        return file_path

    def _resolve_directory(self, dir_path, endpoint):#right now its possible to write in somone else's directory without it being shared
        try:
            self.storage_logic.stat(dir_path, endpoint)
            return dir_path
        except:
            return self.config['home_dir'] + '/'

    def _resolve_filename(self, file_name):
        return file_name + '_' + self._get_current_user() + '.' + datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S") + '.conflict'

    def handle_locks(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)

        if not lock:
            self.lock_file(file_path, endpoint)
        else:
            if self.is_lock_mine(lock):
                self.lock_file(file_path, endpoint)
            if self.is_lock_expired(lock):
                self.lock_file(file_path, endpoint)
        return

    def get_lock(self, file_path):
        lock = self._get_lock(file_path, None) #todo: test endpoint
        if not lock:
            raise LockNotFoundError("Lock not found for file: " + file_path)
        if self.is_lock_mine(lock):
            raise LockNotFoundError("Lock belongs to the user")
        if self.is_lock_expired(lock):
            raise LockNotFoundError("Lock is expired")
        return lock

    def _get_current_user(self):
<<<<<<< HEAD
        user = self.cs3_api.WhoAmI(request=cs3gw.WhoAmIRequest(token=self.auth.authenticate()),
                                   metadata=self._get_token())
        return user.user

    def _get_token(self):
        return [('x-access-token', self.auth.authenticate())]
>>>>>>> c3f5ea6 (Locking for shares part 1 #11)
=======
        if self.user == None:
            self.user = self.cs3_api.WhoAmI(request=cs3gw.WhoAmIRequest(token=self.auth.authenticate()),
                                   metadata=[('x-access-token', self.auth.authenticate())])
        return self.user.user
>>>>>>> 185a219 (*WIP* minor fixes)

    def _get_lock(self, file_path, endpoint):
        metadata = self.storage_logic.get_metadata(file_path, endpoint)
        if not metadata:
            return
        return json.loads(list(metadata.values())[0])