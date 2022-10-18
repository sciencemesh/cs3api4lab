import json
import time
import datetime
import urllib.parse

from cs3api4lab.locks.base import LockBase
from cs3api4lab.exception.exceptions import FileLockedError


class Metadata(LockBase):

    def __init__(self, log, config):
        super().__init__(log, config)
        self.log = log
        self.locks_expiration_time = self.config.locks_expiration_time

    def handle_locks(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)
        if not lock:
            self._set_lock(file_path, endpoint)
            return
        else:
            if self._is_lock_mine(lock) or self._is_lock_expired(lock):
                self._set_lock(file_path, endpoint)
                return
        raise FileLockedError("File %s is locked" % file_path)

    def _generate_lock_entry(self):
        user = self.get_current_user()
        return {self.lock_name: urllib.parse.quote(json.dumps({
            "username": user.username,
            "idp": user.id.idp,
            "opaque_id": user.id.opaque_id,
            "updated": time.time(),
            "created": time.time()
        }))}

    def _set_lock(self, file_path, endpoint):
        self.storage_api.set_metadata(self._generate_lock_entry(), file_path, endpoint)

    def is_valid_external_lock(self, file_path, endpoint):
        lock = self._get_lock(file_path, endpoint)
        is_mine = self._is_lock_mine(lock)
        return lock and not is_mine and not self._is_lock_expired(lock)

    def _is_lock_mine(self, lock):
        user = self.get_current_user()
        if lock:
            return lock['username'] == user.username and lock['idp'] == user.id.idp and lock[
                'opaque_id'] == user.id.opaque_id
        return False

    def _is_lock_expired(self, lock):
        if not lock:
            return True
        return (time.time() - lock['updated']) > datetime.timedelta(seconds=self.locks_expiration_time).total_seconds()

    def _get_lock(self, file_path, endpoint):
        lock = None
        metadata = self.storage_api.get_metadata(file_path, endpoint)
        if metadata:
            lock = json.loads(urllib.parse.unquote(list(metadata.values())[0]))
        return lock

