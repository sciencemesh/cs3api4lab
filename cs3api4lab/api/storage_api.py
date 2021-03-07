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


class StorageApi:

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        # self.locks_api = LocksApi(self.log)

    def read_file(self, file_path, endpoint=None):
        time_start = time.time()
        #
        # Prepare endpoint
        #
        reference = file_utils.get_reference(file_path, endpoint)
        req = cs3sp.InitiateFileDownloadRequest(ref=reference)
        init_file_download = self.cs3_api.InitiateFileDownload(request=req, metadata=[
            ('x-access-token', self.auth.authenticate())])

        if init_file_download.status.code == cs3code.CODE_NOT_FOUND:
            self.log.info('msg="File not found on read" filepath="%s"' % file_path)
            raise IOError('No such file or directory')

        elif init_file_download.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileDownload on read" filepath="%s" reason="%s"' % file_path,
                           init_file_download.status.message)
            raise IOError(init_file_download.status.message)

        self.log.debug(
            'msg="readfile: InitiateFileDownloadRes returned" protocols="%s"' % init_file_download.protocols)

        #
        # Download
        #
        file_get = None
        try:
            protocol = [p for p in init_file_download.protocols if p.protocol == "simple"][0]
            headers = {
                'x-access-token': self.auth.authenticate(),
                'X-Reva-Transfer': protocol.token  # needed if the downloads pass through the data gateway in reva
            }
            file_get = requests.get(url=protocol.download_endpoint, headers=headers)
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

    def write_file(self, file_path, content, endpoint=None):
        """
        Write a file using the given userid as access token. The entire content is written
        and any pre-existing file is deleted (or moved to the previous version if supported).
        """
        #
        # Prepare endpoint
        #
        time_start = time.time()
        reference = file_utils.get_reference(file_path, endpoint)

        if isinstance(content, str):
            content_size = str(len(content))
        else:
            content_size = str(len(content.decode('utf-8')))

        meta_data = types.Opaque(
            map={"Upload-Length": types.OpaqueEntry(decoder="plain", value=str.encode(content_size))})
        req = cs3sp.InitiateFileUploadRequest(ref=reference, opaque=meta_data)
        init_file_upload_res = self.cs3_api.InitiateFileUpload(request=req, metadata=[
            ('x-access-token', self.auth.authenticate())])

        if init_file_upload_res.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileUpload on write" file_path="%s" reason="%s"' % \
                           (file_path, init_file_upload_res.status.message))
            raise IOError(init_file_upload_res.status.message)

        self.log.debug(
            'msg="writefile: InitiateFileUploadRes returned" protocols="%s"' % init_file_upload_res.protocols)

        #
        # Upload
        #
        try:
            protocol = [p for p in init_file_upload_res.protocols if p.protocol == "simple"][0]
            headers = {
                'Tus-Resumable': '1.0.0',
                'File-Path': file_path,
                'File-Size': content_size,
                'x-access-token': self.auth.authenticate(),
                'X-Reva-Transfer': protocol.token
            }
            put_res = requests.put(url=protocol.upload_endpoint, data=content, headers=headers)

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
