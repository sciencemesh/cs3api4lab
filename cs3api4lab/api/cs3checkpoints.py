import urllib
from datetime import datetime

import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.v1beta1.code_pb2 as cs3code
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp

import grpc
from jupyter_server.services.contents.checkpoints import Checkpoints

from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.locks.factory import LockApiFactory
from cs3api4lab.utils.file_utils import FileUtils
from traitlets.config import HasTraits

class CS3Checkpoints(Checkpoints):
    cs3_api = None
    auth = None
    file_api = None
    lock_api = None
    cs3_config = None

    def __init__(self, parent, log, config, **kwargs):
        super().__init__(**kwargs)
        HasTraits.__init__(self, **kwargs)
        self.parent = parent
        self.log = log
        self.cs3_config = config
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)

        self.auth = Auth.get_authenticator(config=self.cs3_config, log=self.log)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        self.file_api = Cs3FileApi(log)
        self.lock_api = LockApiFactory.create(log, self.cs3_config)

    def list_checkpoints(self, path):
        ref = FileUtils.get_reference(path)
        request = cs3sp.ListFileVersionsRequest(ref=ref)
        response = self.cs3_api.ListFileVersions(request=request,
                                                 metadata=[('x-access-token', self.auth.authenticate())])

        if response.status.code != cs3code.CODE_OK:
            self.log.error(f"msg=\"Failed to list file versions\" filepath={path}")

        checkpoints = []
        for i in reversed(range(len(response.versions) - 1)):
            if self.cs3_config.dev_env:  # we need this until https://github.com/cs3org/reva/issues/3928 is resolved
                last_modified = datetime.fromtimestamp(response.versions[i].mtime / 1000.0)
            else:
                last_modified = datetime.fromtimestamp(response.versions[i].mtime)

            # because the checkpoint url is parsed by regular expression, so we need to replace the '.' sign from key
            key = str(response.versions[i].key).replace('.', '-')

            checkpoints.append({
                'id': key,
                'last_modified': last_modified
            })

        return checkpoints

    def restore_checkpoint(self, contents_mgr, checkpoint_id, path):
        #because the checkpoint url is parsed by regular expression, so we need to replace the '.' sign from key
        checkpoint_id = str(checkpoint_id).replace('-', '.')
        if self.cs3_config.dev_env:  # we need this until https://github.com/cs3org/reva/issues/3927 is fixed
            checkpoint_id = 'v' + checkpoint_id

        file_info = self.file_api.stat_info(path)
        # additional request until this issue is resolved https://github.com/cs3org/reva/issues/3243
        if self.cs3_config.dev_env and "/home/" in file_info['filepath']:
            opaque_id = urllib.parse.unquote(file_info['inode']['opaque_id'])
            storage_id = urllib.parse.unquote(file_info['inode']['storage_id'])
            file_info = self.file_api.stat_info(opaque_id, storage_id)

        ref = FileUtils.get_reference(path, self.cs3_config.endpoint)
        request = cs3sp.RestoreFileVersionRequest(ref=ref, key=checkpoint_id)

        if self.cs3_config.locks_api == "metadata":
            if self.lock_api.is_file_locked(file_info):
                self.log.error(f"File {path} is locked and cannot be restored")
                raise IOError(f"File {path} is locked and cannot be restored")
        elif self.cs3_config.locks_api == "cs3":
            if self.lock_api.is_file_locked(file_info):
                lock_response = self.lock_api.get_lock(ref)
                request = cs3sp.RestoreFileVersionRequest(ref=ref, key=checkpoint_id,
                                                          lock_id=lock_response.lock.lock_id)

        response = self.cs3_api.RestoreFileVersion(request=request,
                                                   metadata=[('x-access-token', self.auth.authenticate())])

        if response.status.code != cs3code.CODE_OK:
            self.log.error(f"msg=\"Failed to restore file version\" filepath={path} version={checkpoint_id}")
            raise IOError(response.status.message)


    def create_checkpoint(self, contents_mgr, path):
        return {'id': 'checkpoint', 'last_modified': "0"}

    def rename_checkpoint(self, checkpoint_id, old_path, new_path):
       pass

    def delete_checkpoint(self, checkpoint_id, path):
       pass