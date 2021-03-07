import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.v1beta1.code_pb2 as cs3code
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp
import cs3.storage.provider.v1beta1.resources_pb2 as cs3spr
import grpc
from cs3api4lab.api.file_utils import FileUtils as file_utils
from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
import json
import time
from cs3api4lab.api.cs3_user_api import Cs3UserApi
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.api.storage_api import StorageApi


class LocksApi:
    lock_validity_s = 60
    locks_file_id = '/.locks'

    def __init__(self, log, config=None):
        self.log = log
        if config:
            self.config = config
        else:
            self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        self.user_api = Cs3UserApi(log)
        self.storage_api = StorageApi(self.log)
        return

    def get_copies_info(self, file_id, endpoint):
        ref = self.get_unified_file_ref(file_id, endpoint)
        stat = self.stat(ref)
        copies_info = []
        for lock in stat.info.arbitrary_metadata.metadata:
            if lock.startswith('copy-'):
                if stat.info.arbitrary_metadata.metadata[lock] != '':
                    copies_info.append(json.loads(stat.info.arbitrary_metadata.metadata[lock]))
        return copies_info

    # determine who has the oldest and still valid lock
    def get_merger(self, file_id, endpoint):
        copies_info = list(filter(lambda c: self._is_copy_valid(c), self.get_copies_info(file_id, endpoint)))
        if not copies_info:
            return None
        else:
            t = time.time()
            merger = None
            for m in copies_info:
                if m['created'] < t:
                    t = m['created']
                    merger = m
        return merger

    # add lock on file opening
    def on_open_hook(self, file_path, endpoint):
        self.log.info('Opening ' + endpoint + file_path)
        if self._get_lock_name() in file_path:
            # assume this is a copy
            self.update_lock(file_path, endpoint)
        else:
            # check if it is a shared file
            # todo check if viewer
            if self.is_shared_file(file_path, endpoint):
                ref = self.get_unified_file_ref(file_path, endpoint)
                copy_path = self._get_copy_path(ref)
                copy_stat = self.stat(ref=cs3spr.Reference(path=copy_path))
                if copy_stat.status.code == cs3code.CODE_NOT_FOUND:
                    self.create_working_copy(ref)
                elif copy_stat.status.code == cs3code.CODE_OK:
                    self.update_lock(copy_stat.info.id.opaque_id, copy_stat.info.id.storage_id)

    # clear lock on closing file
    def on_close_hook(self, file_id, endpoint):
        user = self._get_current_user()
        if 'copy-' + user.username in file_id:
            self.delete_lock(file_id, endpoint)

    # remove info about users lock on the original file
    def delete_lock(self, file_id, endpoint):
        self.log.info('Deleting lock for: ' + endpoint + file_id)
        original_ref = self._get_original_ref(file_id, endpoint)
        lock_name = self._get_lock_name()
        empty_lock = {lock_name: ''}
        self.set_metadata(original_ref, empty_lock)
        return

    # copy the shared file content into new file and set lock entry on the original file,
    # add path entry to local locks file
    def create_working_copy(self, original_ref):
        self.log.info('Creating woring copy for ' + original_ref.path)
        copy_info = self.copy_file(original_ref)
        copy_file_ref = self.get_unified_file_ref(copy_info.info.id.opaque_id,
                                                  copy_info.info.id.storage_id)
        original_ref = self.get_unified_file_ref(original_ref.path, self.config['endpoint'])
        original_stat = self.stat(original_ref)
        self.set_metadata(copy_file_ref, {"original": json.dumps({
            "storage_id": original_stat.info.id.storage_id,
            "opaque_id": original_stat.info.id.opaque_id
        })})
        self.set_metadata(original_ref, self._get_lock_entry(copy_info))
        self.add_to_locks_file(original_ref)

    def copy_file(self, original_ref):
        content = ''
        for chunk in self.storage_api.read_file(original_ref.path, self.config['endpoint']):
            content += chunk.decode('utf-8')
        path = self._get_copy_path(original_ref)
        stat = self.stat(ref=cs3spr.Reference(path=path))
        if stat.status.code == cs3code.CODE_OK:
            return stat
        else:
            self.storage_api.write_file(path, content, self.config['endpoint'])
            stat = self.stat(ref=cs3spr.Reference(path=path))
        return stat

    # delete invalid locks on shared files
    def check_locks(self):
        path = self.config['home_dir'] + self.locks_file_id
        stat = self.stat(ref=cs3spr.Reference(path=path))
        if stat.status.code == cs3code.CODE_OK:
            shared_files = self.get_locks_file_content()
            for file_path in shared_files:
                ref = cs3spr.Reference(path=file_path)
                stat = self.stat(ref=ref)
                for lock in stat.info.arbitrary_metadata.metadata:
                    if lock.startswith('copy-'):
                        if not self._is_valid(stat.info.arbitrary_metadata.metadata, lock):
                            if stat.info.arbitrary_metadata.metadata[lock]:
                                self.log.info('Deleting unused lock: ' + lock + ' for file: ' + file_path)
                                self.set_metadata(ref, {lock: ''})

    def add_lock(self, file_id, endpoint):
        copy_stat = self.stat(ref=cs3spr.Reference(id=cs3spr.ResourceId(storage_id=file_id,
                                                                        opaque_id=endpoint)))
        original_ref = self._get_original_ref(file_id, endpoint)
        self.set_metadata(original_ref, self._get_lock_entry(copy_stat))
        return

    # updates lock on the original file using file copy path
    def update_lock(self, file_id, endpoint):
        self.log.info('Updating lock for ' + endpoint + file_id)
        original_ref = self._get_original_ref(file_id, endpoint)
        original_stat = self.stat(ref=original_ref)
        copy_stat = self.stat(ref=cs3spr.Reference(id=cs3spr.ResourceId(storage_id=file_id,
                                                                        opaque_id=endpoint)))
        lock_name = self._get_lock_name()
        if not original_stat.info.arbitrary_metadata.metadata[lock_name]:
            self.set_metadata(original_ref, self._get_lock_entry(copy_stat))
        else:
            lock_content = json.loads(original_stat.info.arbitrary_metadata.metadata[lock_name])
            lock_content['updated'] = time.time()
            self.set_metadata(original_ref, {lock_name: json.dumps(lock_content)})

    def add_to_locks_file(self, original_file_ref):
        path = self.config['home_dir'] + self.locks_file_id
        stat = self.stat(ref=cs3spr.Reference(path=path))
        if stat.status.code != cs3code.CODE_OK:
            self.storage_api.write_file(path, json.dumps([original_file_ref.path]), self.config['endpoint'])
        else:
            locks = self.get_locks_file_content()
            if original_file_ref.path not in locks:
                locks.append(original_file_ref.path)
                self.storage_api.write_file(path, json.dumps(locks), self.config['endpoint'])

    def _get_original_ref(self, file_id, endpoint):
        copy_ref = self.get_unified_file_ref(file_id, endpoint)
        copy_stat = self.stat(ref=copy_ref)
        if not copy_stat.info.arbitrary_metadata.metadata['original']:
            raise Exception("File " + endpoint + file_id + " has no original set")
        original_id = json.loads(copy_stat.info.arbitrary_metadata.metadata['original'])
        original_ref = self.get_unified_file_ref(original_id['opaque_id'], original_id['storage_id'])
        return original_ref

    def _get_copy_path(self, original_ref):
        file_path = original_ref.path.split('/')[-1]
        file_name = file_path.split('.')
        return self.config['home_dir'] + '/' + self._get_lock_name() + file_name[0] + '.' + file_name[-1]

    def set_metadata(self, ref, entry):
        set_metadata_response = self.cs3_api.SetArbitraryMetadata(
            request=cs3sp.SetArbitraryMetadataRequest(
                ref=ref,
                arbitrary_metadata=cs3spr.ArbitraryMetadata(metadata=entry)),
            metadata=self._get_token())
        if set_metadata_response.status.code != cs3code.CODE_OK:
            raise Exception('Unable to set metadata for: ' + ref.path + ' ' + set_metadata_response.status)

    def get_unified_file_ref(self, file_id, endpoint):
        ref = file_utils.get_reference(file_id, endpoint)
        stat = self.stat(ref)
        if stat.status.code == cs3code.CODE_NOT_FOUND:
            return None
        else:
            stat_unified = self.stat(ref=cs3spr.Reference(
                id=cs3spr.ResourceId(storage_id=stat.info.id.storage_id,
                                     opaque_id=stat.info.id.opaque_id)))
            return cs3spr.Reference(path=stat_unified.info.path)

    def _get_current_user(self):
        return self.cs3_api.WhoAmI(request=cs3gw.WhoAmIRequest(token=self.auth.authenticate()),
                                   metadata=self._get_token()).user

    def stat(self, ref):
        return self.cs3_api.Stat(request=cs3sp.StatRequest(ref=ref),
                                 metadata=self._get_token())

    def _get_lock_entry(self, copy_info):
        user = self._get_current_user()
        return {self._get_lock_name(): json.dumps({
            "username": user.username,
            "idp": user.id.idp,
            "opaque_id": user.id.opaque_id,
            "copy_info": {
                "storage_id": copy_info.info.id.storage_id,
                "opaque_id": copy_info.info.id.opaque_id
            },
            "updated": time.time(),
            "created": time.time()
        })}

    def _get_lock_name(self):
        user = self._get_current_user()
        return 'copy-' + user.username + '_' + user.id.idp + '_' + user.id.opaque_id + '_'

    def is_shared_file(self, file_path, endpoint):
        import cs3api4lab.api.cs3_share_api as s
        share_api = s.Cs3ShareApi(self.log, self.config, self.auth)
        stat = self.stat(self.get_unified_file_ref(file_path, endpoint))
        shares = share_api.list().shares
        for share in shares:
            if share.resource_id.storage_id == stat.info.id.storage_id and share.resource_id.opaque_id == stat.info.id.opaque_id.replace('fileid-%2F', 'fileid-'):
                return True
        shares_received = share_api.get_received_shares().shares
        for share in shares_received:
            if share.share.resource_id.storage_id == stat.info.id.storage_id and share.share.resource_id.opaque_id == stat.info.id.opaque_id.replace('fileid-%2F', 'fileid-'):
                return True
        return False

    def _create_locks_file(self):
        self.storage_api.write_file(self.config['home_dir'] + self.locks_file_id, '', self.config['endpoint'])

    def get_locks_file_content(self):
        path = self.config['home_dir'] + self.locks_file_id
        content = ''
        for chunk in self.storage_api.read_file(path, self.config['endpoint']):
            content += chunk.decode('utf-8')
        return json.loads(content)

    def _is_valid(self, metadata, lock):
        lock_content = metadata[lock]
        return bool(lock_content and (time.time() - json.loads(lock_content)['updated'] < self.lock_validity_s))

    def _is_copy_valid(self, copy):
        return time.time() - copy['updated'] < self.lock_validity_s

    def _get_token(self):
        return [('x-access-token', self.auth.authenticate())]
