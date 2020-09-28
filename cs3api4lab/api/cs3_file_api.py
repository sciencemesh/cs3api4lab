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
import requests
from cs3api4lab.auth.authenticator import Authenticator
from cs3api4lab.api.file_utils import FileUtils as file_utils
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager


class Cs3FileApi:
    log = None
    cs3_stub = None
    auth = None
    config = None

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().config
        self.auth = Authenticator()
        channel = ChannelConnector().channel
        self.cs3_stub = cs3gw_grpc.GatewayAPIStub(channel)
        return

    def stat(self, file_id, user_id, endpoint=None):
        """
        Stat a file and returns (size, mtime) as well as other extended info using the given userid as access token.
        Note that endpoint here means the storage id. Note that fileid can be either a path (which MUST begin with /)
        or an id (which MUST NOT start with a /).
        """
        time_start = time.time()
        ref = file_utils.get_reference(file_id, self.config['home_dir'], endpoint)
        stat_info = self.cs3_stub.Stat(request=cs3sp.StatRequest(ref=ref),
                                       metadata=[('x-access-token', self.auth.authenticate(user_id))])
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
                'mtime': stat_info.info.mtime.seconds
            }

        self.log.info('msg="Failed stat" fileid="%s" reason="%s"' % (file_id, stat_info.status.message))
        raise IOError(stat_info.status.message)

    def read_file(self, file_path, user_id, endpoint=None):
        """
        Read a file using the given userid as access token.
        """
        time_start = time.time()
        #
        # Prepare endpoint
        #
        reference = file_utils.get_reference(file_path, self.config['home_dir'], endpoint)
        req = cs3sp.InitiateFileDownloadRequest(ref=reference)
        init_file_download = self.cs3_stub.InitiateFileDownload(request=req, metadata=[
            ('x-access-token', self.auth.authenticate(user_id))])

        if init_file_download.status.code == cs3code.CODE_NOT_FOUND:
            self.log.info('msg="File not found on read" filepath="%s"' % file_path)
            raise IOError('No such file or directory')

        elif init_file_download.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileDownload on read" filepath="%s" reason="%s"' % file_path,
                           init_file_download.status.message)
            raise IOError(init_file_download.status.message)

        self.log.debug(
            'msg="readfile: InitiateFileDownloadRes returned" endpoint="%s"' % init_file_download.download_endpoint)

        #
        # Download
        #
        file_get = None
        try:
            file_get = requests.get(url=init_file_download.download_endpoint,
                                    headers={'x-access-token': self.auth.authenticate(user_id)})
        except requests.exceptions.RequestException as e:
            self.log.error('msg="Exception when downloading file from Reva" reason="%s"' % e)
            raise IOError(e)

        time_end = time.time()
        data = file_get.content

        if file_get.status_code != http.HTTPStatus.OK:
            self.log.error('msg="Error downloading file from Reva" code="%d" reason="%s"' % (
                file_get.status_code, file_get.reason))
            raise IOError(file_get.reason)
        else:
            self.log.info('msg="File open for read" filepath="%s" elapsedTimems="%.1f"' % (
                file_path, (time_end - time_start) * 1000))
            for i in range(0, len(data), int(self.config['chunk_size'])):
                yield data[i:i + int(self.config['chunk_size'])]

    def write_file(self, file_path, user_id, content, endpoint=None):
        """
        Write a file using the given userid as access token. The entire content is written
        and any pre-existing file is deleted (or moved to the previous version if supported).
        """
        #
        # Prepare endpoint
        #
        time_start = time.time()
        reference = file_utils.get_reference(file_path, self.config['home_dir'], endpoint)

        if isinstance(content, str):
            content_size = str(len(content))
        else:
            content_size = str(len(content.decode('utf-8')))

        meta_data = types.Opaque(
            map={"Upload-Length": types.OpaqueEntry(decoder="plain", value=str.encode(content_size))})
        req = cs3sp.InitiateFileUploadRequest(ref=reference, opaque=meta_data)
        init_file_upload_res = self.cs3_stub.InitiateFileUpload(request=req, metadata=[
            ('x-access-token', self.auth.authenticate(user_id))])

        if init_file_upload_res.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileUpload on write" file_path="%s" reason="%s"' % \
                           (file_path, init_file_upload_res.status.message))
            raise IOError(init_file_upload_res.status.message)

        self.log.debug(
            'msg="writefile: InitiateFileUploadRes returned" endpoint="%s"' % init_file_upload_res.upload_endpoint)

        #
        # Upload
        #
        try:
            headers = {
                'Tus-Resumable': '1.0.0',
                'File-Path': file_path,
                'File-Size': content_size,
                'x-access-token': self.auth.authenticate(user_id),
                'X-Reva-Transfer': init_file_upload_res.token
            }
            put_res = requests.put(url=init_file_upload_res.upload_endpoint, data=content, headers=headers)

        except requests.exceptions.RequestException as e:
            self.log.error('msg="Exception when uploading file to Reva" reason="%s"' % e)
            raise IOError(e)

        time_end = time.time()

        if put_res.status_code != http.HTTPStatus.OK:
            self.log.error(
                'msg="Error uploading file to Reva" code="%d" reason="%s"' % (put_res.status_code, put_res.reason))
            raise IOError(put_res.reason)

        self.log.info(
            'msg="File open for write" filepath="%s" elapsedTimems="%.1f"' % (
                file_path, (time_end - time_start) * 1000))

    def remove(self, file_path, user_id, endpoint=None):
        """
        Remove a file or container using the given userid as access token.
        """

        reference = file_utils.get_reference(file_path, self.config['home_dir'], endpoint)
        req = cs3sp.DeleteRequest(ref=reference)
        res = self.cs3_stub.Delete(request=req, metadata=[('x-access-token', self.auth.authenticate(user_id))])

        if res.status.code == cs3code.CODE_NOT_FOUND:
            self.log.info('msg="File or folder not found on remove" filepath="%s"' % file_path)
            raise FileNotFoundError('No such file or directory')

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to remove file or folder" filepath="%s" error="%s"' % (file_path, res))
            raise IOError(res.status.message)

        self.log.debug('msg="Invoked remove" result="%s"' % res)

    def read_directory(self, path, user_id, endpoint=None):
        """
        Read a directory.
        """
        tstart = time.time()
        reference = file_utils.get_reference(path, self.config['home_dir'], endpoint)
        req = cs3sp.ListContainerRequest(ref=reference, arbitrary_metadata_keys="*")
        res = self.cs3_stub.ListContainer(request=req, metadata=[('x-access-token', self.auth.authenticate(user_id))])

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

    def move(self, source_path, destination_path, user_id, endpoint=None):
        """
        Move a file or container.
        """
        tstart = time.time()
        src_reference = file_utils.get_reference(source_path, self.config['home_dir'], endpoint)
        dest_reference = file_utils.get_reference(destination_path, self.config['home_dir'], endpoint)

        req = cs3sp.MoveRequest(source=src_reference, destination=dest_reference)
        res = self.cs3_stub.Move(request=req, metadata=[('x-access-token', self.auth.authenticate(user_id))])

        if res.status.code != cs3code.CODE_OK:
            self.log.error('msg="Failed to move" source="%s" destination="%s" reason="%s"' % (
                source_path, destination_path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug('msg="Invoked move" source="%s" destination="%s" elapsedTimems="%.1f"' % (
            source_path, destination_path, (tend - tstart) * 1000))

    def create_directory(self, path, user_id, endpoint=None):
        """
        Create a directory.
        """
        tstart = time.time()
        reference = file_utils.get_reference(path, self.config['home_dir'], endpoint)
        req = cs3sp.CreateContainerRequest(ref=reference)
        res = self.cs3_stub.CreateContainer(request=req, metadata=[('x-access-token', self.auth.authenticate(user_id))])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to create container" filepath="%s" reason="%s"' % (path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug(
            'msg="Invoked create container" filepath="%s" elapsedTimems="%.1f"' % (path, (tend - tstart) * 1000))
