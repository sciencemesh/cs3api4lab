"""
cs3_file_api.py

CS3 File API for the JupyterLab Extension

Authors:
"""
import http
import time
import urllib.parse
import grpc
import requests

import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.v1beta1.code_pb2 as cs3code
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp
from google.protobuf.json_format import MessageToDict

from cs3api4lab.exception.exceptions import ResourceNotFoundError

from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.api.storage_api import StorageApi
from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.locks.factory import LockApiFactory


class Cs3FileApi:
    log = None
    cs3_api = None
    auth = None
    config = None
    lock_api = None

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        self.storage_api = StorageApi(log)
        self.lock_api = LockApiFactory.create(log, self.config)

    def mount_point(self):
        """
        This returns current mount point for the user
        """
        request = cs3sp.GetHomeRequest()
        response = self.cs3_api.GetHome(request)
        return {
            "path": response.path
        }

    def stat_info(self, file_path, endpoint='/'):
        """
        Stat a file and returns (size, mtime) as well as other extended info using the given userid as access token.
        Note that endpoint here means the storage id. Note that fileid can be either a path (which MUST begin with /)
        or an id (which MUST NOT start with a /).
        """
        time_start = time.time()
        stat = self.storage_api.stat(file_path, endpoint)

        if stat.status.code == cs3code.CODE_NOT_FOUND:
            self.log.info('msg="Failed stat" fileid="%s" reason="%s"' % (file_path, stat.status.message))
            raise FileNotFoundError(stat.status.message + ", file " + file_path)

        if stat.status.code != cs3code.CODE_OK:
            self._handle_error(stat)

        time_end = time.time()
        self.log.info('msg="Invoked stat" fileid="%s" elapsedTimems="%.1f"' % (file_path, (time_end - time_start) * 1000))
        return {
            'inode': {'storage_id': stat.info.id.storage_id,
                      'opaque_id': stat.info.id.opaque_id},
            'filepath': stat.info.path,
            'userid': stat.info.owner.opaque_id,
            'size': stat.info.size,
            'mtime': stat.info.mtime.seconds,
            'type': stat.info.type,
            'mime_type': stat.info.mime_type,
            'idp': stat.info.owner.idp,
            'permissions': stat.info.permission_set,
            'arbitrary_metadata': MessageToDict(stat.info.arbitrary_metadata),
        }
        
    def read_file(self, stat, endpoint=None):
        """
        Read a file using the given userid as access token.
        """
        if stat:
            # additional request until this issue is resolved https://github.com/cs3org/reva/issues/3243
            if self.config.dev_env and "/home/" in stat['filepath']:
                opaque_id = urllib.parse.unquote(stat['inode']['opaque_id'])
                storage_id = urllib.parse.unquote(stat['inode']['storage_id'])
                stat = self.stat_info(opaque_id, storage_id)

            try:
                self.lock_api.set_lock(stat)
            except IOError:
                self.log.info("File %s locked, opening in read-only mode" % stat['filepath'])

        else:
            msg = "%s: %s" % (stat.status.code, stat.status.message)
            self.log.error('msg="Error when stating file for read" reason="%s"' % msg)
            raise IOError('Error when stating file')

        init_file_download = self.storage_api.init_file_download(stat['filepath'], endpoint)
        try:
            file_get = self.storage_api.download_content(init_file_download)
        except requests.exceptions.RequestException as e:
            self.log.error('msg="Exception when downloading file from Reva" reason="%s"' % e)
            raise IOError(e)

        size = len(file_get.content)
        chunk_size = self.config.chunk_size
        for i in range(0, size, chunk_size):
            yield file_get.content[i:i + self.config.chunk_size]

    def write_file(self, file_path, content, endpoint=None, format=None):
        """
        Write a file using the given userid as access token. The entire content is written
        and any pre-existing file is deleted (or moved to the previous version if supported).
        """
        time_start = time.time()

        stat = None
        try:
            stat = self.stat_info(file_path, endpoint)
            if stat:
                # additional request until this issue is resolved https://github.com/cs3org/reva/issues/3243
                if self.config.dev_env and "/home/" in stat['filepath']:
                    opaque_id = urllib.parse.unquote(stat['inode']['opaque_id'])
                    storage_id = urllib.parse.unquote(stat['inode']['storage_id'])
                    stat = self.stat_info(opaque_id, storage_id)

                # file_path = self.lock_manager.resolve_file_path(stat)
        except Exception as e:
            self.log.info('Creating new file %s', file_path)

        if stat:
            # fixme - this might cause overwriting/locking issues due to unexpected error codes
            self.lock_api.set_lock(stat)

        content_size = FileUtils.calculate_content_size(content, format)
        init_file_upload = self.storage_api.init_file_upload(file_path, endpoint, content_size)

        try:
            upload_response = self.storage_api.upload_content(file_path, content, content_size, init_file_upload)

        except requests.exceptions.RequestException as e:
            self.log.error('msg="Exception when uploading file to Reva" reason="%s"' % e)
            raise IOError(e)

        time_end = time.time()

        if upload_response.status_code != http.HTTPStatus.OK:
            self.log.error(
                'msg="Error uploading file to Reva" code="%d" reason="%s"' % (upload_response.status_code, upload_response.reason))
            raise IOError(upload_response.reason)

        self.log.info(
            'msg="File open for write" filepath="%s" elapsedTimems="%.1f"' % (
                file_path, (time_end - time_start) * 1000))

        return file_path

    def remove(self, file_path, endpoint=None):
        """
        Remove a file or container using the given userid as access token.
        """

        reference = FileUtils.get_reference(file_path, endpoint)
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
        tstart = time.time()
        reference = FileUtils.get_reference(path, endpoint)
        req = cs3sp.ListContainerRequest(ref=reference)
        res = self.cs3_api.ListContainer(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code == cs3code.CODE_NOT_FOUND:
            raise ResourceNotFoundError(f"directory {path} not found")

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to read container" filepath="%s" reason="%s"' % (path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug(
            'msg="Invoked read container" filepath="%s" elapsedTimems="%.1f"' % (path, (tend - tstart) * 1000))

        out = []
        for info in res.infos:
            if self.config.mount_dir != '/' and len(self.config.mount_dir) > 0 and info.path.startswith(self.config.mount_dir):
                info.path = info.path.rsplit(self.config.mount_dir)[-1]
            out.append(info)
        return out

    def move(self, source_path, destination_path, endpoint=None):
        """
        Move a file or container.
        """
        tstart = time.time()
        src_reference = FileUtils.get_reference(source_path, endpoint)
        dest_reference = FileUtils.get_reference(destination_path, endpoint)

        # fixme - this might cause overwriting issues due to unexpected error codes
        stat = self.storage_api.stat(destination_path, endpoint)
        if stat.status.code == cs3code.CODE_OK:
            self.log.error('msg="Failed to move" source="%s" destination="%s" reason="%s"' % (
                source_path, destination_path, "file already exists"))
            raise IOError("file already exists")

        req = cs3sp.MoveRequest(source=src_reference, destination=dest_reference)
        res = self.cs3_api.Move(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code == cs3code.CODE_NOT_FOUND:
            raise ResourceNotFoundError(f"source {source_path} not found")

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
        reference = FileUtils.get_reference(path, endpoint)
        req = cs3sp.CreateContainerRequest(ref=reference)
        res = self.cs3_api.CreateContainer(request=req, metadata=[('x-access-token', self.auth.authenticate())])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to create container" filepath="%s" reason="%s"' % (path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug(
            'msg="Invoked create container" filepath="%s" elapsedTimems="%.1f"' % (path, (tend - tstart) * 1000))

    def get_home_dir(self):
        return self.config.home_dir if self.config.home_dir else ""

    def _handle_error(self, response):
        self.log.error(response)
        raise Exception("Incorrect server response: " +
                        response.status.message)
