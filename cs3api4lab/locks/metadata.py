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

    def set_lock(self, stat):
        if not self.is_file_locked(stat):
            self.storage_api.set_metadata(self.lock_name, self._generate_lock_entry(), stat)
        else:
            raise FileLockedError("File %s is locked" % stat['filepath'])

    def is_file_locked(self, stat):
        file_is_locked = True

        lock = self._get_lock(stat)
        if not lock:
            file_is_locked = False
        elif self._is_lock_mine(lock) or self._is_lock_expired(lock):
            file_is_locked = False

        return file_is_locked

    def _generate_lock_entry(self):
        user = self.get_current_user()
        return urllib.parse.quote(json.dumps({
            "username": user.username,
            "idp": user.id.idp,
            "opaque_id": user.id.opaque_id,
            "updated": time.time(),
            "created": time.time()
        }))

    def is_valid_external_lock(self, stat):
        lock = self._get_lock(stat)
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

    def _get_lock(self, stat):
        if not stat['arbitrary_metadata']:
            return None

        if not stat['arbitrary_metadata']['metadata'].get(self.lock_name):
            return None

        lock = stat['arbitrary_metadata']['metadata'].get(self.lock_name)
        return json.loads(urllib.parse.unquote(lock))