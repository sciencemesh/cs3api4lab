from notebook.base.handlers import APIHandler
from tornado import gen, web
import json

from cs3api4lab.api.cs3apismanager import CS3APIsManager
from cs3api4lab.api.cs3_share_api import Cs3ShareApi


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
        RequestHandler.handle_request(self, self.share_api.list, 200)


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
        request = self.get_json_body()
        RequestHandler.handle_request(self, self.share_api.list_grantees_for_file, 200, request['storage_id'], request['file_path'])


handlers = [
    (r"/api/cs3/shares", ShareHandler),
    (r"/api/cs3/shares/list", ListSharesHandler),
    (r"/api/cs3/shares/received", ListReceivedSharesHandler),
    (r"/api/cs3/shares/file", ListSharesForFile),
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
