import grpc
import requests

import cs3.storage.provider.v1beta1.resources_pb2 as storage_provider
import cs3.types.v1beta1.types_pb2 as types
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp
import cs3.rpc.v1beta1.code_pb2 as cs3code
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import webdav3.client as webdav

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager

from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.auth.authenticator import Auth


class StorageApi:
    log = None
    cs3_api = None
    auth = None
    config = None

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager.get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)
        return

    def get_unified_file_ref(self, file_path, endpoint):
        stat = self.stat(file_path, endpoint)
        if stat.status.code != cs3code.CODE_OK:
            return None
        else:
            stat_unified = self._stat_internal(ref=storage_provider.Reference(
                resource_id=storage_provider.ResourceId(storage_id=stat.info.id.storage_id,
                                                        opaque_id=stat.info.id.opaque_id)))
            return storage_provider.Reference(path=stat_unified.info.path)

    def stat(self, file_path, endpoint='/'):
        ref = FileUtils.get_reference(file_path, endpoint)
        return self._stat_internal(ref)

    def _stat_internal(self, ref):
        return self.cs3_api.Stat(request=cs3sp.StatRequest(ref=ref),
                                 metadata=[('x-access-token', self.auth.authenticate())])

    def set_metadata(self, data, file_path, endpoint):
        ref = self.get_unified_file_ref(file_path, endpoint)
        set_metadata_response = self.cs3_api.SetArbitraryMetadata(
            request=cs3sp.SetArbitraryMetadataRequest(
                ref=ref,
                arbitrary_metadata=storage_provider.ArbitraryMetadata(metadata=data)),
            metadata=self._get_token())
        if set_metadata_response.status.code != cs3code.CODE_OK:
            raise Exception('Unable to set metadata for: ' + file_path + ' ' + str(set_metadata_response.status))

    def get_metadata(self, file_path, endpoint):
        ref = self.get_unified_file_ref(file_path, endpoint)
        if ref:
            stat = self._stat_internal(ref)
            if stat.status.code == cs3code.CODE_OK:
                return stat.info.arbitrary_metadata.metadata
        return None

    def init_file_upload(self, file_path, endpoint, content_size):
        reference = FileUtils.get_reference(file_path, endpoint)
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

        return init_file_upload_res

    def upload_content(self, file_path, content, content_size, init_file_upload_response):
        protocol = [p for p in init_file_upload_response.protocols if p.protocol == "simple"][0]
        if self.config.tus_enabled:
            headers = {
                'Tus-Resumable': '1.0.0',
                'File-Path': file_path,
                'File-Size': content_size,
                'x-access-token': self.auth.authenticate(),
                'X-Reva-Transfer': protocol.token
            }
        else:
            headers = {
                'x-access-token': self.auth.authenticate(),
                'Upload-Length': content_size,
                'X-Reva-Transfer': protocol.token
            }
        put_res = requests.put(url=protocol.upload_endpoint, data=content, headers=headers)

        return put_res

    def init_file_download(self, file_path, endpoint):
        reference = FileUtils.get_reference(file_path, endpoint)
        req = cs3sp.InitiateFileDownloadRequest(ref=reference)

        init_file_download_response = self.cs3_api.InitiateFileDownload(request=req, metadata=[
            ('x-access-token', self.auth.authenticate())])

        if init_file_download_response.status.code == cs3code.CODE_NOT_FOUND:
            self.log.info('msg="File not found on read" filepath="%s"' % file_path)
            raise IOError('No such file or directory')

        elif init_file_download_response.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileDownload on read" filepath="%s" reason="%s"' % file_path,
                           init_file_download_response.status.message)
            raise IOError(init_file_download_response.status.message)

        self.log.debug(
            'msg="readfile: InitiateFileDownloadRes returned" protocols="%s"' % init_file_download_response.protocols)

        return init_file_download_response

    def download_content(self, init_file_download):
        protocol = [p for p in init_file_download.protocols if p.protocol == "simple"][0]
        # if file is shared via OCM the request needs to go through webdav
        if protocol.opaque and init_file_download.protocols[0].opaque.map['webdav-file-path'].value:
            download_url = protocol.download_endpoint + str(protocol.opaque.map['webdav-file-path'].value, 'utf-8')[1:]
            file_get = webdav.Client({}).session.request(
                method='GET',
                url=download_url,
                headers={
                    'X-Access-Token': str(protocol.opaque.map['webdav-token'].value, 'utf-8')}
            )
        else:
            headers = {
                'x-access-token': self.auth.authenticate(),
                'X-Reva-Transfer': protocol.token  # needed if the downloads pass through the data gateway in reva
            }
            file_get = requests.get(url=protocol.download_endpoint, headers=headers)
        return file_get

    def _get_token(self):
        return [('x-access-token', self.auth.authenticate())]
