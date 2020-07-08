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
	ctx = {}  # "map" to store some module context: cf. init()
	tokens = {}  # map userid [string] to {authentication token, token expiration time}

	def __init__(self, config, log):
		"""
		Init module-level variables
		"""
		self.ctx['log'] = log
		self.ctx['chunksize'] = int(config['chunksize'])
		self.ctx['authtokenvalidity'] = int(config['authtokenvalidity'])

		reva_host = config['revahost']

		# prepare the gRPC connection
		ch = grpc.insecure_channel(reva_host)
		self.ctx['cs3stub'] = cs3gw_grpc.GatewayAPIStub(ch)
		return

	def __authenticate(self, userid):

		"""
		Obtain a token from Reva for the given userid
		"""

		# ToDo: use real authentication data
		# authReq = cs3gw.AuthenticateRequest(type='bearer', client_secret=userid)
		authReq = cs3gw.AuthenticateRequest(type='basic', client_id='einstein', client_secret='relativity')

		if userid not in self.tokens or self.tokens[userid]['exp'] < time.time():
			authRes = self.ctx['cs3stub'].Authenticate(authReq)
			self.tokens[userid] = {'tok': authRes.token, 'exp': time.time() + self.ctx['authtokenvalidity']}

		# piggy back on the opportunity to expire old tokens, but asynchronously
		# as to not impact the current session: let's use python3.7's coroutines support
		# asyncio.run(_async_cleanuptokens())

		return self.tokens[userid]['tok']

	def __cs3_reference(self, endpoint, fileid):

		if endpoint == 'default':
			raise IOError('A CS3API-compatible storage endpoint must be identified by a storage UUID')

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
		tstart = time.time()

		ref = self.__cs3_reference(endpoint, fileid)

		statInfo = self.ctx['cs3stub'].Stat(request=cs3sp.StatRequest(ref=ref),
											metadata=[('x-access-token', self.__authenticate(userid))])

		tend = time.time()
		self.ctx['log'].info('msg="Invoked stat" fileid="%s" elapsedTimems="%.1f"' % (fileid, (tend - tstart) * 1000))

		if statInfo.status.code == cs3code.CODE_OK:
			self.ctx['log'].debug('msg="Stat result" data="%s"' % statInfo)
			return {
				'inode': statInfo.info.id.storage_id + ':' + statInfo.info.id.opaque_id,
				'filepath': statInfo.info.path,
				'userid': statInfo.info.owner.opaque_id,
				'size': statInfo.info.size,
				'mtime': statInfo.info.mtime.seconds
			}

		self.ctx['log'].info('msg="Failed stat" fileid="%s" reason="%s"' % (fileid, statInfo.status.message))
		raise IOError(statInfo.status.message)

	def stat_x(self, endpoint, fileid, userid):
		"""
		Get extended stat info (inode, filepath, userid, size, mtime). Equivalent to stat.
		"""

		return self.stat(endpoint, fileid, userid)

	def set_x_attr(self, endpoint, filepath, userid, key, value):
		"""Set the extended attribute <key> to <value> using the given userid as access token"""

		reference = self.__cs3_reference(endpoint, filepath)

		arbitrary_metadata = cs3spr.ArbitraryMetadata()
		arbitrary_metadata.metadata.update({key: str(value)})

		req = cs3sp.SetArbitraryMetadataRequest(ref=reference, arbitrary_metadata=arbitrary_metadata)

		res = self.ctx['cs3stub'].SetArbitraryMetadata(request=req,
													   metadata=[('x-access-token', self.__authenticate(userid))])
		if res.status.code != cs3code.CODE_OK:
			self.ctx['log'].warning('msg="Failed to getxattr" filepath="%s" key="%s" reason="%s"' % (filepath, key, res.status.message))
			raise IOError(res.status.message)

	def get_x_attr(self, endpoint, filepath, userid, key):
		"""
		Get the extended attribute <key> using the given userid as access token. Do not raise exceptions
		"""
		tstart = time.time()
		reference = self.__cs3_reference(endpoint, filepath)

		statInfo = self.ctx['cs3stub'].Stat(request=cs3sp.StatRequest(ref=reference),
											metadata=[('x-access-token', self.__authenticate(userid))])
		tend = time.time()

		if statInfo.status.code != cs3code.CODE_OK:
			self.ctx['log'].warning('msg="Failed to stat" filepath="%s" key="%s" reason="%s"' % (filepath, key, statInfo.status.message))
			raise IOError(statInfo.status.message)
		try:
			xattrvalue = statInfo.info.arbitrary_metadata.metadata[key]
			if xattrvalue == '':
				raise KeyError

			self.ctx['log'].debug('msg="Invoked stat for getxattr" filepath="%s" elapsedTimems="%.1f"' % (filepath, (tend - tstart) * 1000))
			return xattrvalue

		except KeyError:
			self.ctx['log'].info('msg="Key not found in getxattr" filepath="%s" key="%s"' % (filepath, key))
			return None

	def remove_x_attr(self, endpoint, filepath, userid, key):
		"""
		Remove the extended attribute <key> using the given userid as access token
		"""

		reference = self.__cs3_reference(endpoint, filepath)

		req = cs3sp.UnsetArbitraryMetadataRequest(ref=reference, arbitrary_metadata_keys=[key])
		res = self.ctx['cs3stub'].UnsetArbitraryMetadata(request=req, metadata=[('x-access-token', self.__authenticate(userid))])

		if res.status.code != cs3code.CODE_OK:
			self.ctx['log'].warning('msg="Failed to rmxattr" filepath="%s" key="%s" exception="%s"' % (filepath, key, res.status.message))
			raise IOError(res.status.message)

		self.ctx['log'].debug('msg="Invoked rmxattr" result="%s"' % res)

	def read_file(self, endpoint, filepath, userid):
		"""
		Read a file using the given userid as access token. Note that the function is a generator, managed by Flask.
		"""

		tstart = time.time()

		#
		# Prepare endpoint
		#
		reference = self.__cs3_reference(endpoint, filepath)

		req = cs3sp.InitiateFileDownloadRequest(ref=reference)

		initfiledownloadres = self.ctx['cs3stub'].InitiateFileDownload(request=req, metadata=[('x-access-token', self.__authenticate(userid))])

		if initfiledownloadres.status.code == cs3code.CODE_NOT_FOUND:
			self.ctx['log'].info('msg="File not found on read" filepath="%s"' % filepath)
			yield IOError('No such file or directory')

		elif initfiledownloadres.status.code != cs3code.CODE_OK:
			self.ctx['log'].debug('msg="Failed to initiateFileDownload on read" filepath="%s" reason="%s"' % \
								  (filepath, initfiledownloadres.status.message))
			yield IOError(initfiledownloadres.status.message)

		self.ctx['log'].debug('msg="readfile: InitiateFileDownloadRes returned" endpoint="%s"' % initfiledownloadres.download_endpoint)

		#
		# Download
		#
		file_get = None
		try:
			file_get = requests.get(url=initfiledownloadres.download_endpoint, headers={'x-access-token': self.__authenticate(userid)})
		except requests.exceptions.RequestException as e:
			self.ctx['log'].error('msg="Exception when downloading file from Reva" reason="%s"' % e)
			yield IOError(e)

		tend = time.time()
		data = file_get.content

		if file_get.status_code != http.HTTPStatus.OK:
			self.ctx['log'].error('msg="Error downloading file from Reva" code="%d" reason="%s"' % (file_get.status_code, file_get.reason))
			print("->>>>>> CS3APIsManager read_file error: ")
			print(file_get)
			print(data)
			print(self.ctx['log'])
			yield IOError(file_get.reason)
		else:
			self.ctx['log'].info('msg="File open for read" filepath="%s" elapsedTimems="%.1f"' % (filepath, (tend - tstart) * 1000))
			print("->>>>>> CS3APIsManager read_file OK: ")
			print(file_get)
			print(data)
			print(self.ctx['log'])
			for i in range(0, len(data), self.ctx['chunksize']):
				yield data[i:i + self.ctx['chunksize']]

	def write_file(self, endpoint, filepath, userid, content, noversion=0):
		"""
		Write a file using the given userid as access token. The entire content is written
		and any pre-existing file is deleted (or moved to the previous version if supported).
		The noversion flag is currently not supported.
		"""

		#
		# Prepare endpoint
		#
		tstart = time.time()

		reference = self.__cs3_reference(endpoint, filepath)

		req = cs3sp.InitiateFileUploadRequest(ref=reference)
		initfileuploadres = self.ctx['cs3stub'].InitiateFileUpload(request=req, metadata=[('x-access-token', self.__authenticate(userid))])

		if initfileuploadres.status.code != cs3code.CODE_OK:
			self.ctx['log'].debug('msg="Failed to initiateFileUpload on write" filepath="%s" reason="%s"' % \
								  (filepath, initfileuploadres.status.message))
			raise IOError(initfileuploadres.status.message)

		self.ctx['log'].debug('msg="writefile: InitiateFileUploadRes returned" endpoint="%s"' % initfileuploadres.upload_endpoint)

		#
		# Upload
		#
		try:
			# TODO: Use tus client instead of PUT
			headers = {
				'Tus-Resumable': '1.0.0',
				'x-access-token': self.__authenticate(userid)
			}
			putres = requests.put(url=initfileuploadres.upload_endpoint, data=content, headers=headers)

		except requests.exceptions.RequestException as e:
			self.ctx['log'].error('msg="Exception when uploading file to Reva" reason="%s"' % e)
			raise IOError(e)

		tend = time.time()

		if putres.status_code != http.HTTPStatus.OK:
			self.ctx['log'].error('msg="Error uploading file to Reva" code="%d" reason="%s"' % (putres.status_code, putres.reason))
			raise IOError(putres.reason)

		self.ctx['log'].info('msg="File open for write" filepath="%s" elapsedTimems="%.1f"' % (filepath, (tend - tstart) * 1000))

	def remove_file(self, endpoint, filepath, userid, force=0):
		"""
		Remove a file using the given userid as access token.
		The force argument is ignored for now for CS3 storage.
		"""

		reference = self.__cs3_reference(endpoint, filepath)

		req = cs3sp.DeleteRequest(ref=reference)
		res = self.ctx['cs3stub'].Delete(request=req, metadata=[('x-access-token', self.__authenticate(userid))])

		if res.status.code != cs3code.CODE_OK:
			self.ctx['log'].warning('msg="Failed to remove file" filepath="%s" error="%s"' % (filepath, res))
			raise IOError(res.status.message)

		self.ctx['log'].debug('msg="Invoked removefile" result="%s"' % res)

	def read_directory(self, endpoint, filepath, userid):

		"""
		Read a directory.
		"""

		tstart = time.time()

		reference = self.__cs3_reference(endpoint, filepath)

		req = cs3sp.ListContainerRequest(ref=reference, arbitrary_metadata_keys="*")
		res = self.ctx['cs3stub'].ListContainer(request=req, metadata=[('x-access-token', self.__authenticate(userid))])

		if res.status.code != cs3code.CODE_OK:
			self.ctx['log'].warning('msg="Failed to read container" filepath="%s" reason="%s"' % (filepath, res.status.message))
			raise IOError(res.status.message)

		tend = time.time()
		self.ctx['log'].info('msg="Invoked read container" filepath="%s" elapsedTimems="%.1f"' % (filepath, (tend - tstart) * 1000))

		out = []
		for info in res.infos:
			out.append(info)

		return out
