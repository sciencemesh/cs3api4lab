from notebook.base.handlers import APIHandler
from tornado import gen, web
import json

from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.api.cs3_public_share_api import Cs3PublicShareApi


class ShareHandler(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def post(self):
        request = self.get_json_body()
        RequestHandler.handle_request(self,
                                      self.share_api.create,
                                      201,
                                      request['endpoint'],
                                      request['file_path'],
                                      request['grantee'],
                                      request['idp'],
                                      request['role'],
                                      request['grantee_type'])

    @web.authenticated
    @gen.coroutine
    def delete(self):
        share_id = self.get_query_argument('share_id')
        RequestHandler.handle_request(self, self.share_api.remove, 204, share_id)

    def put(self):
        request = self.get_json_body()
        RequestHandler.handle_request(self,
                                      self.share_api.update,
                                      204,
                                      request['share_id'],
                                      request['role'])


class ListSharesHandler(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        RequestHandler.handle_request(self, self.share_api.list_dir_model, 200)


class ListReceivedSharesHandler(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        RequestHandler.handle_request(self, self.share_api.list_received, 200)

    @web.authenticated
    @gen.coroutine
    def put(self):
        share_id = self.get_query_argument('share_id', default=None)
        state = self.get_query_argument('state', default='pending')
        RequestHandler.handle_request(self, self.share_api.update_received, 200, share_id, state)


class ListSharesForFile(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        file_path = self.get_query_argument('file_path')
        RequestHandler.handle_request(self, self.share_api.list_grantees_for_file, 200, file_path)

class PublicSharesHandler(APIHandler):
    @property
    def public_share_api(self):
        return Cs3PublicShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        token = self.get_query_argument('token', default=None)
        opaque_id = self.get_query_argument('opaque_id')
        RequestHandler.handle_request(self, self.public_share_api.get_public_share, 200, opaque_id, token)

    @web.authenticated
    @gen.coroutine
    def post(self):
        request = self.get_json_body()
        RequestHandler.handle_request(self,
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
        RequestHandler.handle_request(self, self.public_share_api.remove_public_share, 204, opaque_id)

    @web.authenticated
    @gen.coroutine
    def put(self):
        request = self.get_json_body()
        RequestHandler.handle_request(self, self.public_share_api.update_public_share,
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
        RequestHandler.handle_request(self, self.public_share_api.get_public_share_by_token, 200, token, password)

class ListPublicSharesHandler(APIHandler):
    @property
    def public_share_api(self):
        return Cs3PublicShareApi(self.log)

    @web.authenticated
    @gen.coroutine
    def get(self):
        RequestHandler.handle_request(self, self.public_share_api.list_public_shares, 200)

handlers = [
    (r"/api/cs3/shares", ShareHandler),
    (r"/api/cs3/shares/list", ListSharesHandler),
    (r"/api/cs3/shares/received", ListReceivedSharesHandler),
    (r"/api/cs3/shares/file", ListSharesForFile),
    (r"/api/cs3/public/shares", PublicSharesHandler),
    (r"/api/cs3/public/shares/list", ListPublicSharesHandler),
    (r"/api/cs3/public/share", GetPublicShareByTokenHandler)
]


class RequestHandler(APIHandler):

    @staticmethod
    def handle_request(self, api_function, success_code, *args):
        try:
            response = api_function(*args)
        except Exception as err:
            RequestHandler.handle_error(self, err)
        else:
            RequestHandler.handle_response(self, response, success_code)

    @staticmethod
    def handle_error(self, err):
        # todo specify errors and response codes
        self.set_status(500)
        self.finish(json.dumps(str(err)))

    @staticmethod
    def handle_response(self, response, success_code):
        self.set_header('Content-Type', 'application/json')
        self.set_status(success_code)
        if response is None:
            self.finish()
        else:
            self.finish(json.dumps(response))
