import json

from jupyter_server.base.handlers import APIHandler
from tornado import gen, web
from grpc._channel import _InactiveRpcError
from cs3api4lab.exception.exceptions import *
from cs3api4lab.api.share_api_facade import ShareAPIFacade
from cs3api4lab.api.cs3_public_share_api import Cs3PublicShareApi
from cs3api4lab.api.cs3_user_api import Cs3UserApi
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from jupyter_server.utils import url_path_join
from cs3api4lab.utils.asyncify import get_or_create_eventloop

class ShareHandler(APIHandler):
    @property
    def share_api(self):
        return ShareAPIFacade(self.log)

    @web.authenticated
    @gen.coroutine
    def post(self):
        request = self.get_json_body()
        try:
            yield RequestHandler.async_handle_request(self,
                                                      self.share_api.create,
                                                      201,
                                                      request['endpoint'],
                                                      request['file_path'],
                                                      request['grantee'],
                                                      request['idp'],
                                                      request['role'],
                                                      request['grantee_type'])
        except KeyError as err:
            RequestHandler.handle_error(self, ParamError(err))

    @web.authenticated
    @gen.coroutine
    def delete(self):
        share_id = self.get_query_argument('share_id')
        yield RequestHandler.async_handle_request(self, self.share_api.remove, 204, share_id)

    @web.authenticated
    @gen.coroutine
    def put(self):
        params = self.get_json_body()
        try:
            yield RequestHandler.async_handle_request(self,
                                          self.share_api.update_share,
                                          204,
                                          params)
        except KeyError as err:
            RequestHandler.handle_error(self, ParamError(err))


class ListSharesHandler(APIHandler):
    @property
    def share_api(self):
        return ShareAPIFacade(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        yield RequestHandler.async_handle_request(self, self.share_api.list_shares, 200)


class ListReceivedSharesHandler(APIHandler):
    @property
    def share_api(self):
        return ShareAPIFacade(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        status = self.get_query_argument('status', default=None)

        yield RequestHandler.async_handle_request(self, self.share_api.list_received, 200, status)

    @web.authenticated
    @gen.coroutine
    def put(self):
        body = self.get_json_body()
        yield RequestHandler.async_handle_request(self, self.share_api.update_received, 200, body["share_id"], body["state"])


class ListSharesForFile(APIHandler):
    @property
    def share_api(self):
        return ShareAPIFacade(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        file_path = self.get_query_argument('file_path')
        yield RequestHandler.async_handle_request(self, self.share_api.list_grantees_for_file, 200, file_path)

class SharedFolder(APIHandler):
    @property
    def file_api(self):
        return Cs3FileApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        yield RequestHandler.async_handle_request(self, self.file_api.list_shared_folder, 200)


class HomeDirHandler(APIHandler):
    @property
    def file_api(self):
        return Cs3FileApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        yield RequestHandler.async_handle_request(self, self.file_api.get_home_dir, 200)

class PublicSharesHandler(APIHandler):
    @property
    def public_share_api(self):
        return Cs3PublicShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        token = self.get_query_argument('token', default=None)
        opaque_id = self.get_query_argument('opaque_id')
        yield RequestHandler.async_handle_request(self, self.public_share_api.get_public_share, 200, opaque_id, token)

    @web.authenticated
    @gen.coroutine
    def post(self):
        request = self.get_json_body()
        yield RequestHandler.async_handle_request(self,
                                                  self.public_share_api.create_public_share,
                                                  201,
                                                  request['endpoint'],
                                                  request['file_path'],
                                                  request['password'],
                                                  request['exp_date'],
                                                  request['permissions'])

    @web.authenticated
    @gen.coroutine
    def delete(self):
        opaque_id = self.get_query_argument('opaque_id')
        yield RequestHandler.async_handle_request(self, self.public_share_api.remove_public_share, 204, opaque_id)

    @web.authenticated
    @gen.coroutine
    def put(self):
        request = self.get_json_body()
        yield RequestHandler.async_handle_request(self, self.public_share_api.update_public_share,
                                                  204,
                                                  request['opaque_id'],
                                                  request['token'],
                                                  request['field_type'],
                                                  request['field_value'])


class GetPublicShareByTokenHandler(APIHandler):
    @property
    def public_share_api(self):
        return Cs3PublicShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        token = self.get_query_argument('token')
        password = self.get_query_argument('password', default='')
        yield RequestHandler.async_handle_request(self, self.public_share_api.get_public_share_by_token, 200, token, password)


class ListPublicSharesHandler(APIHandler):
    @property
    def public_share_api(self):
        return Cs3PublicShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        yield RequestHandler.async_handle_request(self, self.public_share_api.list_public_shares, 200)


class UserInfoHandler(APIHandler):
    @property
    def user_api(self):
        return Cs3UserApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        idp = self.get_query_argument('idp')
        opaque_id = self.get_query_argument('opaque_id')
        yield RequestHandler.async_handle_request(self, self.user_api.get_user, 200, idp, opaque_id)

class UserInfoClaimHandler(APIHandler):
    @property
    def user_api(self):
        return Cs3UserApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        claim = self.get_query_argument('claim')
        value = self.get_query_argument('value')
        yield RequestHandler.async_handle_request(self, self.user_api.get_user_info_by_claim, 200, claim, value)

class UserQueryHandler(APIHandler):
    @property
    def user_api(self):
        return Cs3UserApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        query = self.get_query_argument('query')
        yield RequestHandler.async_handle_request(self, self.user_api.find_users_by_query, 200, query)

def setup_handlers(web_app, url_path):
    handlers = [
        (r"/api/cs3/shares", ShareHandler),
        (r"/api/cs3/shares/list", ListSharesHandler),
        (r"/api/cs3/shares/received", ListReceivedSharesHandler),
        (r"/api/cs3/shares/file", ListSharesForFile),
        (r"/api/cs3/shares/shared_folder", SharedFolder),
        (r"/api/cs3/public/shares", PublicSharesHandler),
        (r"/api/cs3/public/shares/list", ListPublicSharesHandler),
        (r"/api/cs3/public/share", GetPublicShareByTokenHandler),
        (r"/api/cs3/user", UserInfoHandler),
        (r"/api/cs3/user/claim", UserInfoClaimHandler),
        (r"/api/cs3/user/query", UserQueryHandler),
        (r"/api/cs3/user/home_dir", HomeDirHandler)
    ]

    for handler in handlers:
        pattern = url_path_join(web_app.settings['base_url'], handler[0])
        new_handler = tuple([pattern] + list(handler[1:]))
        web_app.add_handlers('.*$', [new_handler])

class RequestHandler(APIHandler):

    @staticmethod
    def handle_request(self, api_function, success_code, *args):
        try:
            response = api_function(*args)
        except Exception as err:
            self.log.error(err)
            RequestHandler.handle_error(self, err)
        else:
            RequestHandler.handle_response(self, response, success_code)

    @staticmethod
    async def async_handle_request(self, api_function, success_code, *args):
        try:
            loop = get_or_create_eventloop()
            response = await loop.run_in_executor(None, api_function, *args)
        except Exception as err:
            self.log.error(err)
            RequestHandler.handle_error(self, err)
        else:
            RequestHandler.handle_response(self, response, success_code)

    @staticmethod
    def handle_error(self, err):
        status = RequestHandler.get_response_code(err)
        response = {
            'error_message': '%s: %s' % (str(status), err.message if hasattr(err, 'message') else str(err))
        }
        self.set_header('Content-Type', 'application/json')
        self.set_status(status)
        self.finish(json.dumps(response))

    @staticmethod
    def handle_response(self, response, success_code):
        self.set_header('Content-Type', 'application/json')
        self.set_status(success_code)
        if response is None:
            self.finish()
        else:
            self.finish(json.dumps(response))

    @staticmethod
    def get_response_code(err):
        if isinstance(err, ShareAlreadyExistsError):
            return 409
        if isinstance(err, (ShareNotFoundError, LockNotFoundError)):
            return 404
        if isinstance(err, (InvalidTypeError, KeyError, FileNotFoundError, ParamError)):
            return 400
        if isinstance(err, OCMDisabledError):
            return 501
        if isinstance(err, _InactiveRpcError):
            return 503
        return 500
