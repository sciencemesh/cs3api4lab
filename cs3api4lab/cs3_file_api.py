"""
cs3_file_api.py

CS3 File API for the JupyterLab Extension

Authors:
"""

import http
import time

import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.code_pb2 as cs3code
import cs3.storage.provider.v1beta1.provider_api_pb2 as cs3sp
import cs3.storage.provider.v1beta1.resources_pb2 as cs3spr
import grpc
import requests


class Cs3FileApi:
    
    tokens = {}  # map userid [string] to {authentication token, token expiration time}

    log = None
    chunksize = 4194304
    authtokenvalidity = 3600
    cs3_stub = None

    client_id = None
    client_secret = None

    def __init__(self, config, log):

        self.log = log
        self.chunksize = int(config['chunksize'])
        self.authtokenvalidity = int(config['authtokenvalidity'])

        secure_channel = config['secure_channel']
        reva_host = config['revahost']

        self.client_id = config['client_id']
        self.client_secret = config['client_secret']

        # prepare the gRPC connection

        if secure_channel:

            try:

                cert = open(config['client_cert'], 'rb').read()
                key = open(config['client_key'], 'rb').read()

                ca_cert = open(config['ca_cert'], 'rb').read()
                credentials = grpc.ssl_channel_credentials(ca_cert, key, cert)

                ch = grpc.secure_channel(reva_host, credentials)

            except():
                print("Error create secure channel")
                raise

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

    def _cs3_reference(self, endpoint, fileid):
        if fileid[0] == '/':
            # assume this is a filepath
            ref = cs3spr.Reference(path=fileid)
        else:
            # assume we have an opaque fileid
            ref = cs3spr.Reference(id=cs3spr.ResourceId(storage_id=endpoint, opaque_id=fileid))
        return ref

    def stat(self, endpoint, fileid, userid):

        """
        Stat a file and returns (size, mtime) as well as other extended info using the given userid as access token.
        Note that endpoint here means the storage id. Note that fileid can be either a path (which MUST begin with /), or an id (which MUST NOT
        start with a /).
        """

        if endpoint == 'default':
            raise IOError('A CS3API-compatible storage endpoint must be identified by a storage UUID')

        time_start = time.time()

        ref = self._cs3_reference(endpoint, fileid)

        stat_info = self.cs3_stub.Stat(request=cs3sp.StatRequest(ref=ref),
                                       metadata=[('x-access-token', self._authenticate(userid))])

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

    def stat_x(self, endpoint, fileid, userid):
        """
        Get extended stat info (inode, filepath, userid, size, mtime). Equivalent to stat.
        """

        return self.stat(endpoint, fileid, userid)

    def set_x_attr(self, endpoint, filepath, userid, key, value):
        """Set the extended attribute <key> to <value> using the given userid as access token"""

        reference = self._cs3_reference(endpoint, filepath)

        arbitrary_metadata = cs3spr.ArbitraryMetadata()
        arbitrary_metadata.metadata.update({key: str(value)})

        req = cs3sp.SetArbitraryMetadataRequest(ref=reference, arbitrary_metadata=arbitrary_metadata)

        res = self.cs3_stub.SetArbitraryMetadata(request=req,
                                                 metadata=[('x-access-token', self._authenticate(userid))])
        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to getxattr" filepath="%s" key="%s" reason="%s"' % (filepath, key, res.status.message))
            raise IOError(res.status.message)

    def get_x_attr(self, endpoint, filepath, userid, key):
        """
        Get the extended attribute <key> using the given userid as access token. Do not raise exceptions
        """
        time_start = time.time()
        reference = self._cs3_reference(endpoint, filepath)

        stat_info = self.cs3_stub.Stat(request=cs3sp.StatRequest(ref=reference),
                                       metadata=[('x-access-token', self._authenticate(userid))])
        time_end = time.time()

        if stat_info.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to stat" filepath="%s" key="%s" reason="%s"' % (filepath, key, stat_info.status.message))
            raise IOError(stat_info.status.message)
        try:
            xattrvalue = stat_info.info.arbitrary_metadata.metadata[key]
            if xattrvalue == '':
                raise KeyError

            self.log.debug('msg="Invoked stat for getxattr" filepath="%s" elapsedTimems="%.1f"' % (filepath, (time_end - time_start) * 1000))
            return xattrvalue

        except KeyError:
            self.log.info('msg="Key not found in getxattr" filepath="%s" key="%s"' % (filepath, key))
            return None

    def remove_x_attr(self, endpoint, filepath, userid, key):
        """
        Remove the extime_ended attribute <key> using the given userid as access token
        """

        reference = self._cs3_reference(endpoint, filepath)

        req = cs3sp.UnsetArbitraryMetadataRequest(ref=reference, arbitrary_metadata_keys=[key])
        res = self.cs3_stub.UnsetArbitraryMetadata(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to rmxattr" filepath="%s" key="%s" exception="%s"' % (filepath, key, res.status.message))
            raise IOError(res.status.message)

        self.log.debug('msg="Invoked rmxattr" result="%s"' % res)

    def read_file(self, endpoint, filepath, userid):
        """
        Read a file using the given userid as access token.
        """

        time_start = time.time()

        #
        # Prepare endpoint
        #
        reference = self._cs3_reference(endpoint, filepath)

        req = cs3sp.InitiateFileDownloadRequest(ref=reference)

        init_file_download = self.cs3_stub.InitiateFileDownload(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if init_file_download.status.code == cs3code.CODE_NOT_FOUND:
            self.log.info('msg="File not found on read" filepath="%s"' % filepath)
            yield IOError('No such file or directory')

        elif init_file_download.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileDownload on read" filepath="%s" reason="%s"' % \
                                  (filepath, init_file_download.status.message))
            yield IOError(init_file_download.status.message)

        self.log.debug('msg="readfile: InitiateFileDownloadRes returned" endpoint="%s"' % init_file_download.download_endpoint)

        #
        # Download
        #
        file_get = None
        try:
            file_get = requests.get(url=init_file_download.download_endpoint, headers={'x-access-token': self._authenticate(userid)})
        except requests.exceptions.RequestException as e:
            self.log.error('msg="Exception when downloading file from Reva" reason="%s"' % e)
            yield IOError(e)

        time_end = time.time()
        data = file_get.content

        if file_get.status_code != http.HTTPStatus.OK:
            self.log.error('msg="Error downloading file from Reva" code="%d" reason="%s"' % (file_get.status_code, file_get.reason))
            yield IOError(file_get.reason)
        else:
            self.log.info('msg="File open for read" filepath="%s" elapsedTimems="%.1f"' % (filepath, (time_end - time_start) * 1000))
            for i in range(0, len(data), self.chunksize):
                yield data[i:i + self.chunksize]

    def write_file(self, endpoint, filepath, userid, content, noversion=0):
        """
        Write a file using the given userid as access token. The entire content is written
        and any pre-existing file is deleted (or moved to the previous version if supported).
        The noversion flag is currently not supported.
        """

        #
        # Prepare endpoint
        #
        time_start = time.time()

        reference = self._cs3_reference(endpoint, filepath)

        req = cs3sp.InitiateFileUploadRequest(ref=reference)
        initfileuploadres = self.cs3_stub.InitiateFileUpload(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if initfileuploadres.status.code != cs3code.CODE_OK:
            self.log.debug('msg="Failed to initiateFileUpload on write" filepath="%s" reason="%s"' % \
                                  (filepath, initfileuploadres.status.message))
            raise IOError(initfileuploadres.status.message)

        self.log.debug('msg="writefile: InitiateFileUploadRes returned" endpoint="%s"' % initfileuploadres.upload_endpoint)

        #
        # Upload
        #
        try:
            # TODO: Use tus client instead of PUT
            headers = {
                'Tus-Resumable': '1.0.0',
                'x-access-token': self._authenticate(userid)
            }
            putres = requests.put(url=initfileuploadres.upload_endpoint, data=content, headers=headers)

        except requests.exceptions.RequestException as e:
            self.log.error('msg="Exception when uploading file to Reva" reason="%s"' % e)
            raise IOError(e)

        time_end = time.time()

        if putres.status_code != http.HTTPStatus.OK:
            self.log.error('msg="Error uploading file to Reva" code="%d" reason="%s"' % (putres.status_code, putres.reason))
            raise IOError(putres.reason)

        self.log.info('msg="File open for write" filepath="%s" elapsedTimems="%.1f"' % (filepath, (time_end - time_start) * 1000))

    def remove_file(self, endpoint, filepath, userid, force=0):
        """
        Remove a file using the given userid as access token.
        The force argument is ignored for now for CS3 storage.
        """

        reference = self._cs3_reference(endpoint, filepath)

        req = cs3sp.DeleteRequest(ref=reference)
        res = self.cs3_stub.Delete(request=req, metadata=[('x-access-token', self._authenticate(userid))])

        if res.status.code != cs3code.CODE_OK:
            self.log.warning('msg="Failed to remove file" filepath="%s" error="%s"' % (filepath, res))
            raise IOError(res.status.message)

        self.log.debug('msg="Invoked removefile" result="%s"' % res)
