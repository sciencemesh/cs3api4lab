"""
cs3_file_api.py

CS3 File API for the JupyterLab Extension

Authors:
"""

import http
import sys
import time

import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.code_pb2 as cs3code
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp
import cs3.storage.provider.v1beta1.resources_pb2 as cs3spr
import cs3.types.v1beta1.types_pb2 as types
import grpc
import requests


class Cs3FileApi:
    tokens = {}  # map userid [string] to {authentication token, token expiration time}

    log = None
    chunksize = 4194304
    authtokenvalidity = 3600
    cs3_stub = None
    home_dir = ""

    client_id = None
    client_secret = None

    def __init__(self, config, log):

        self.log = log
        self.chunksize = int(config['chunksize'])
        self.authtokenvalidity = int(config['authtokenvalidity'])

        secure_channel = bool(config['secure_channel'])
        reva_host = config['revahost']

        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.home_dir = config['home_dir']

        # prepare the gRPC connection

        if secure_channel:

            try:

                cert = open(config['client_cert'], 'rb').read()
                key = open(config['client_key'], 'rb').read()

                ca_cert = open(config['ca_cert'], 'rb').read()
                credentials = grpc.ssl_channel_credentials(ca_cert, key, cert)

                ch = grpc.secure_channel(reva_host, credentials)

            except:
                ex = sys.exc_info()[0]
                self.log.error('msg="Error create secure channel" reason="%s"' % ex)
                raise IOError(ex)

        else:
            ch = grpc.insecure_channel(reva_host)

        self.cs3_stub = cs3gw_grpc.GatewayAPIStub(ch)
        return

    def _authenticate(self, userid):

        # ToDo: use real authentication data or get token from author provider
        # authReq = cs3gw.AuthenticateRequest(type='bearer', client_secret=userid)

        if userid not in self.tokens or self.tokens[userid]['exp'] < time.time():
            auth_req = cs3gw.AuthenticateRequest(type='basic', client_id=self.client_id, client_secret=self.client_secret)
            auth_res = self.cs3_stub.Authenticate(auth_req)
            self.tokens[userid] = {'tok': auth_res.token, 'exp': time.time() + self.authtokenvalidity}

        # piggy back on the opportunity to expire old tokens, but asynchronously
        # as to not impact the current session: let's use python3.7's coroutines support
        # asyncio.run(_async_cleanuptokens())

        return self.tokens[userid]['tok']

    def _cs3_reference(self, fileid, endpoint=None):

        if len(fileid) > 0 and fileid[0] == '/':

            # assume this is a filepath
            if len(self.home_dir) > 0 and not fileid.startswith(self.home_dir):
                fileid = self.home_dir + fileid

            file = cs3spr.Reference(path=fileid)
            return file

        if endpoint == 'default' or endpoint is None:
            raise IOError('A CS3API-compatible storage endpoint must be identified by a storage UUID')

        # assume we have an opaque fileid
        return cs3spr.Reference(id=cs3spr.ResourceId(storage_id=endpoint, opaque_id=fileid))

    def stat(self, fileid, userid, endpoint=None):

        """
        Stat a file and returns (size, mtime) as well as other extended info using the given userid as access token.
        Note that endpoint here means the storage id. Note that fileid can be either a path (which MUST begin with /), or an id (which MUST NOT
        start with a /).
        """

        time_start = time.time()

        ref = self._cs3_reference(fileid, endpoint)

        stat_info = self.cs3_stub.Stat(request=cs3sp.StatRequest(ref=ref), metadata=[('x-access-token', self._authenticate(userid))])

        time_end = time.time()
        self.log.info('msg="Invoked stat" fileid="%s" elapsedTimems="%.1f"' % (fileid, (time_end - time_start) * 1000))

        if stat_info.status.code == cs3code.CODE_OK:
            self.log.debug('msg="Stat result" data="%s"' % stat_info)
            return {
                'inode': stat_info.info.id.storage_id + ':' + stat_info.info.id.opaque_id,
                'filepath': stat_info.info.path,
                'userid': stat_info.info.owner.opaque_id,
                'size': stat_info.info.size,
                'mtime': stat_info.info.mtime.seconds
            }

        self.log.info('msg="Failed stat" fileid="%s" reason="%s"' % (fileid, stat_info.status.message))
        raise IOError(stat_info.status.message)

    def read_file(self, filepath, userid, endpoint=None):
        """
        Read a file using the given userid as access token.
        """

        time_start = time.time()

        #
        # Prepare endpoint
        #
        reference = self._cs3_reference(filepath, endpoint)

        req = cs3sp.InitiateFileDownloadRequest(ref=reference)

        init_file_download = self.cs3_stub.InitiateFileDownload(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if init_file_download.status.code == cs3code.CODE_NOT_FOUND:
            self.log.info('msg="File not found on read" filepath="%s"' % filepath)
            raise IOError('No such file or directory')

        elif init_file_download.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileDownload on read" filepath="%s" reason="%s"' % filepath, init_file_download.status.message)
            raise IOError(init_file_download.status.message)

        self.log.debug('msg="readfile: InitiateFileDownloadRes returned" endpoint="%s"' % init_file_download.download_endpoint)

        #
        # Download
        #
        file_get = None
        try:
            file_get = requests.get(url=init_file_download.download_endpoint, headers={'x-access-token': self._authenticate(userid)})
        except requests.exceptions.RequestException as e:
            self.log.error('msg="Exception when downloading file from Reva" reason="%s"' % e)
            raise IOError(e)

        time_end = time.time()
        data = file_get.content

        if file_get.status_code != http.HTTPStatus.OK:
            self.log.error('msg="Error downloading file from Reva" code="%d" reason="%s"' % (file_get.status_code, file_get.reason))
            raise IOError(file_get.reason)
        else:
            self.log.info('msg="File open for read" filepath="%s" elapsedTimems="%.1f"' % (filepath, (time_end - time_start) * 1000))
            for i in range(0, len(data), self.chunksize):
                yield data[i:i + self.chunksize]

    def write_file(self, filepath, userid, content, endpoint=None):
        """
        Write a file using the given userid as access token. The entire content is written
        and any pre-existing file is deleted (or moved to the previous version if supported).
        """

        #
        # Prepare endpoint
        #
        time_start = time.time()

        reference = self._cs3_reference(filepath, endpoint)

        if isinstance(content, str):
            content_size = str(len(content))
        else:
            content_size = str(len(content.decode('utf-8')))

        meta_data = types.Opaque(map={"Upload-Length": types.OpaqueEntry(decoder="plain", value=str.encode(content_size))})

        req = cs3sp.InitiateFileUploadRequest(ref=reference, opaque=meta_data)
        init_file_upload_res = self.cs3_stub.InitiateFileUpload(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if init_file_upload_res.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileUpload on write" filepath="%s" reason="%s"' % \
                           (filepath, init_file_upload_res.status.message))
            raise IOError(init_file_upload_res.status.message)

        self.log.debug('msg="writefile: InitiateFileUploadRes returned" endpoint="%s"' % init_file_upload_res.upload_endpoint)

        #
        # Upload
        #
        try:
            headers = {
                'Tus-Resumable': '1.0.0',
                'File-Path': filepath,
                'File-Size': content_size,
                'x-access-token': self._authenticate(userid),
                'X-Reva-Transfer': init_file_upload_res.token
            }
            put_res = requests.put(url=init_file_upload_res.upload_endpoint, data=content, headers=headers)

        except requests.exceptions.RequestException as e:
            self.log.error('msg="Exception when uploading file to Reva" reason="%s"' % e)
            raise IOError(e)

        time_end = time.time()

        if put_res.status_code != http.HTTPStatus.OK:
            self.log.error('msg="Error uploading file to Reva" code="%d" reason="%s"' % (put_res.status_code, put_res.reason))
            raise IOError(put_res.reason)

        self.log.info('msg="File open for write" filepath="%s" elapsedTimems="%.1f"' % (filepath, (time_end - time_start) * 1000))

    def remove(self, filepath, userid, endpoint=None):
        """
        Remove a file or container using the given userid as access token.
        """

        reference = self._cs3_reference(filepath, endpoint)

        req = cs3sp.DeleteRequest(ref=reference)
        res = self.cs3_stub.Delete(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to remove file or folder" filepath="%s" error="%s"' % (filepath, res))
            raise IOError(res.status.message)

        self.log.debug('msg="Invoked remove" result="%s"' % res)

    def read_directory(self, path, userid, endpoint=None):

        """
        Read a directory.
        """

        tstart = time.time()

        reference = self._cs3_reference(path, endpoint)

        req = cs3sp.ListContainerRequest(ref=reference, arbitrary_metadata_keys="*")
        res = self.cs3_stub.ListContainer(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to read container" filepath="%s" reason="%s"' % (path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug('msg="Invoked read container" filepath="%s" elapsedTimems="%.1f"' % (path, (tend - tstart) * 1000))

        out = []
        for info in res.infos:

            if len(self.home_dir) > 0 and info.path.startswith(self.home_dir):
                info.path = info.path.rsplit(self.home_dir)[-1]

            out.append(info)

        return out

    def move(self, source_path, destination_path, userid, endpoint=None):

        """
        Move a file or container.
        """

        tstart = time.time()

        src_reference = self._cs3_reference(source_path, endpoint)
        dest_reference = self._cs3_reference(destination_path, endpoint)

        req = cs3sp.MoveRequest(source=src_reference, destination=dest_reference)
        res = self.cs3_stub.Move(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if res.status.code != cs3code.CODE_OK:
            self.log.error('msg="Failed to move" source="%s" destination="%s" reason="%s"' % (source_path, destination_path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug('msg="Invoked move" source="%s" destination="%s" elapsedTimems="%.1f"' % (source_path, destination_path, (tend - tstart) * 1000))

    def create_directory(self, path, userid, endpoint=None):

        """
        Create a directory.
        """

        tstart = time.time()

        reference = self._cs3_reference(path, endpoint)

        req = cs3sp.CreateContainerRequest(ref=reference)
        res = self.cs3_stub.CreateContainer(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to create container" filepath="%s" reason="%s"' % (path, res.status.message))
            raise IOError(res.status.message)

        tend = time.time()
        self.log.debug('msg="Invoked create container" filepath="%s" elapsedTimems="%.1f"' % (path, (tend - tstart) * 1000))
