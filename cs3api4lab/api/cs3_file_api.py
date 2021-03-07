"""
cs3_file_api.py

CS3 File API for the JupyterLab Extension

Authors:
"""

import http
import time

import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.code_pb2 as cs3code
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp
import cs3.types.v1beta1.types_pb2 as types
import grpc
import requests

from cs3api4lab.api.file_utils import FileUtils as file_utils
from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.api.cs3_locks_api import LocksApi
from cs3api4lab.api.storage_api import StorageApi


class Cs3FileApi:
    log = None
    cs3_api = None
    auth = None
    config = None

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        self.locks_api = LocksApi(self.log)
        self.storage_api = StorageApi(self.log)
        return

    def stat(self, file_id, endpoint=None):
        """
        Stat a file and returns (size, mtime) as well as other extended info using the given userid as access token.
        Note that endpoint here means the storage id. Note that fileid can be either a path (which MUST begin with /)
        or an id (which MUST NOT start with a /).
        """
        time_start = time.time()
        ref = file_utils.get_reference(file_id, endpoint)
        stat_info = self.cs3_api.Stat(request=cs3sp.StatRequest(ref=ref),
                                      metadata=[('x-access-token', self.auth.authenticate())])
        time_end = time.time()
        self.log.info('msg="Invoked stat" fileid="%s" elapsedTimems="%.1f"' % (file_id, (time_end - time_start) * 1000))

        if stat_info.status.code == cs3code.CODE_OK:
            self.log.debug('msg="Stat result" data="%s"' % stat_info)
            return {
                'inode': {'storage_id': stat_info.info.id.storage_id,
                          'opaque_id': stat_info.info.id.opaque_id},
                'filepath': stat_info.info.path,
                'userid': stat_info.info.owner.opaque_id,
                'size': stat_info.info.size,
                'mtime': stat_info.info.mtime.seconds,
                'type': stat_info.info.type,
                'mime_type': stat_info.info.mime_type,
                'idp': stat_info.info.owner.idp,
                'permissions': stat_info.info.permission_set
            }

        self.log.info('msg="Failed stat" fileid="%s" reason="%s"' % (file_id, stat_info.status.message))
        raise FileNotFoundError(stat_info.status.message + ", file " + file_id)

    def read_file(self, file_path, endpoint=None):
        self.locks_api.on_open_hook(file_path, endpoint)
        return self.storage_api.read_file(file_path, endpoint)

    def write_file(self, file_path, content, endpoint=None):
        self.storage_api.write_file(file_path, content, endpoint)

    def remove(self, file_path, endpoint=None):
        """
        Remove a file or container using the given userid as access token.
        """

        reference = file_utils.get_reference(file_path, endpoint)
        req = cs3sp.DeleteRequest(ref=reference)
        res = self.cs3_api.Delete(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code == cs3code.CODE_NOT_FOUND:
            self.log.info('msg="File or folder not found on remove" filepath="%s"' % file_path)
            raise FileNotFoundError('No such file or directory')

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to remove file or folder" filepath="%s" error="%s"' % (file_path, res))
            raise IOError(res.status.message)

        self.log.debug('msg="Invoked remove" result="%s"' % res)

    def read_directory(self, path, endpoint=None):
        """
        Read a directory.
        """
        self.locks_api.check_locks()
        tstart = time.time()
        reference = file_utils.get_reference(path, endpoint)
        req = cs3sp.ListContainerRequest(ref=reference, arbitrary_metadata_keys="*")
        res = self.cs3_api.ListContainer(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to read container" filepath="%s" reason="%s"' % (path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug(
            'msg="Invoked read container" filepath="%s" elapsedTimems="%.1f"' % (path, (tend - tstart) * 1000))

        out = []
        for info in res.infos:
            if len(self.config['home_dir']) > 0 and info.path.startswith(self.config['home_dir']):
                info.path = info.path.rsplit(self.config['home_dir'])[-1]
            out.append(info)
        return out

    def move(self, source_path, destination_path, endpoint=None):
        """
        Move a file or container.
        """
        tstart = time.time()
        src_reference = file_utils.get_reference(source_path, endpoint)
        dest_reference = file_utils.get_reference(destination_path, endpoint)

        req = cs3sp.MoveRequest(source=src_reference, destination=dest_reference)
        res = self.cs3_api.Move(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code != cs3code.CODE_OK:
            self.log.error('msg="Failed to move" source="%s" destination="%s" reason="%s"' % (
                source_path, destination_path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug('msg="Invoked move" source="%s" destination="%s" elapsedTimems="%.1f"' % (
            source_path, destination_path, (tend - tstart) * 1000))

    def create_directory(self, path, endpoint=None):
        """
        Create a directory.
        """
        tstart = time.time()
        reference = file_utils.get_reference(path, endpoint)
        req = cs3sp.CreateContainerRequest(ref=reference)
        res = self.cs3_api.CreateContainer(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to create container" filepath="%s" reason="%s"' % (path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug(
            'msg="Invoked create container" filepath="%s" elapsedTimems="%.1f"' % (path, (tend - tstart) * 1000))
