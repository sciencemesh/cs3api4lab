import time

from cs3api4lab.locks.base import LockBase
from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.exception.exceptions import FileLockedError

import cs3.storage.provider.v1beta1.provider_api_pb2 as storage_api
import cs3.types.v1beta1.types_pb2 as cs3_types
import cs3.identity.user.v1beta1.resources_pb2 as id_res
import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
import cs3.rpc.v1beta1.code_pb2 as cs3code

import google.protobuf.json_format as json_format


class Cs3(LockBase):

    def __init__(self, log, config):
        super().__init__(log, config)

    def set_lock(self, stat):
        ref = FileUtils.get_reference(stat['inode']['opaque_id'], stat['inode']['storage_id'])
        lock = self._get_lock(ref)
        '''
        this if statement should be replaced with self.is_file_locked()  and set_lock
        function after the bug with setting/refreshing locks is resolved 
        '''
        if not lock:
            self._set_lock(ref)
        elif self._is_lock_mine(lock):
            self._refresh_lock(ref)
        else:
            raise FileLockedError("File %s is locked" % stat['filepath'])

    def is_file_locked(self, stat):
        file_is_locked = True

        ref = FileUtils.get_reference(stat['inode']['opaque_id'], stat['inode']['storage_id'])
        lock = self._get_lock(ref)
        if not lock:
           file_is_locked = False
        elif self._is_lock_mine(lock):
            file_is_locked = False

        return file_is_locked

    def is_valid_external_lock(self, stat):
        ref = FileUtils.get_reference(stat['inode']['opaque_id'], stat['inode']['storage_id'])
        lock = self._get_lock(ref)
        return lock and not self._is_lock_mine(lock)

    def _is_lock_mine(self, lock):
        user = self.get_current_user()
        return lock['user']['idp'] == user.id.idp and lock['user']['opaqueId'] == user.id.opaque_id

    def _get_lock(self, ref):
        request = storage_api.GetLockRequest(ref=ref)
        lock_response = self.cs3_api.GetLock(request=request, metadata=[('x-access-token', self.auth.authenticate())])
        if lock_response.status.code == cs3code.CODE_OK:
            return json_format.MessageToDict(lock_response.lock)
        elif lock_response.status.code == cs3code.CODE_NOT_FOUND:
            return None
        else:
            raise IOError("Unable to get lock: %s" % str(lock_response))

    def _unlock(self, ref, lock):
        request = storage_api.UnlockRequest(ref=ref, lock=lock)
        unlock_response = self.cs3_api.Unlock(request=request, metadata=[('x-access-token', self.auth.authenticate())])
        if unlock_response.status.code != cs3code.CODE_OK:
            raise IOError("Unable to unlock: %s" % str(unlock_response))

    def _set_lock(self, ref):
        user = self.get_current_user()
        lock = storage_resources.Lock(
            lock_id=self.lock_name,
            type=storage_resources.LOCK_TYPE_WRITE,
            user=id_res.UserId(idp=user.id.idp, opaque_id=user.id.opaque_id, type=user.id.type),
            expiration=cs3_types.Timestamp(seconds=int(time.time() + self.config.locks_expiration_time))
        )
        request = storage_api.SetLockRequest(ref=ref, lock=lock)
        lock_response = self.cs3_api.SetLock(request=request, metadata=[('x-access-token', self.auth.authenticate())])
        if lock_response.status.code != cs3code.CODE_OK:
            raise IOError("Unable to set lock: %s" % str(lock_response))

    def _refresh_lock(self, ref):
        user = self.get_current_user()
        lock = storage_resources.Lock(
            lock_id=self.lock_name,
            type=storage_resources.LOCK_TYPE_WRITE,
            user=id_res.UserId(idp=user.id.idp, opaque_id=user.id.opaque_id, type=user.type),
            expiration=cs3_types.Timestamp(seconds=int(time.time() + self.config.locks_expiration_time))
        )
        request = storage_api.RefreshLockRequest(ref=ref, lock=lock)
        refresh_response = self.cs3_api.RefreshLock(request=request,
                                                    metadata=[('x-access-token', self.auth.authenticate())])
        if refresh_response.status.code != cs3code.CODE_OK:
            raise IOError("Unable to refresh lock: %s" % str(refresh_response))


