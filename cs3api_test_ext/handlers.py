from typing import Optional, Awaitable

from notebook.base.handlers import APIHandler
from notebook.utils import maybe_future
from tornado import gen, web
import json

from cs3api_test_ext.cs3apismanager import CS3APIsManager
from cs3api_test_ext.cs3_share_api import Cs3ShareApi


class HelloWorldHandle(APIHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @web.authenticated
    @gen.coroutine
    def get(self):
        output = {
            'hello': 'world'
        }
        self.set_header('Content-Type', 'application/json')
        self.finish(json.dumps(output))


class FilesHandle(APIHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @property
    def cs3api_manager(self):
        # return self.settings['cs3api_manager']
        return CS3APIsManager()

    @web.authenticated
    @gen.coroutine
    def get(self, path=""):

        type = self.get_query_argument('type', default=None)
        format = self.get_query_argument('format', default=None)
        content = self.get_query_argument('content', default='1')
        if self.get_query_argument('path', default="") != "":
            path = self.get_query_argument('path', default="")

        # print("-------------------> FilesHandle::get():")
        # print("path: ", path, "content: ", content, "type: ", type, "format: ", format)

        if type not in {None, 'directory', 'file', 'notebook'}:
            raise web.HTTPError(400, u'Type %r is invalid' % type)

        if format not in {None, 'text', 'base64'}:
            raise web.HTTPError(400, u'Format %r is invalid' % format)

        if content not in {'0', '1'}:
            raise web.HTTPError(400, u'Content %r is invalid' % content)
        content = int(content)

        cs3manager = self.cs3api_manager
        model = yield maybe_future(
            cs3manager.get(path=path, type=type, format=format, content=content)
        )

        # print("-------------------> FilesHandle::get():")

        self._finish_model(model)

    @web.authenticated
    @gen.coroutine
    def post(self, path=''):
        """
        Create a new file in the specified path.
        """

        print("-------------------> FilesHandle::post():")
        print("path: ", path)

        # cm = self.contents_manager
        #
        # file_exists = yield maybe_future(cm.file_exists(path))
        # if file_exists:
        #     raise web.HTTPError(400, "Cannot POST to files, use PUT instead.")
        #
        # dir_exists = yield maybe_future(cm.dir_exists(path))
        # if not dir_exists:
        #     raise web.HTTPError(404, "No such directory: %s" % path)
        #
        # model = self.get_json_body()
        #
        # if model is not None:
        #     copy_from = model.get('copy_from')
        #     ext = model.get('ext', '')
        #     type = model.get('type', '')
        #     if copy_from:
        #         yield self._copy(copy_from, path)
        #     else:
        #         yield self._new_untitled(path, type=type, ext=ext)
        # else:
        #     yield self._new_untitled(path)

        print("-------------------> FilesHandle::post():")

    @web.authenticated
    @gen.coroutine
    def put(self, path=''):
        """
        Saves the file in the location specified by name and path.
        """
        print("-------------------> FilesHandle::put():")
        print("path: ", path)

        model = self.get_json_body()

        print("model:", model)
        # if model:
        #     if model.get('copy_from'):
        #         raise web.HTTPError(400, "Cannot copy with PUT, only POST")
        #     exists = yield maybe_future(self.contents_manager.file_exists(path))
        #     if exists:
        #         yield maybe_future(self._save(model, path))
        #     else:
        #         yield maybe_future(self._upload(model, path))
        # else:
        #     yield maybe_future(self._new_untitled(path))

        print("-------------------> FilesHandle::put():")

    @web.authenticated
    @gen.coroutine
    def delete(self, path=''):
        """
        Delete a file in the given path
        """
        print("-------------------> FilesHandle::delete():")
        print("path: ", path)
        print("-------------------> FilesHandle::delete():")

    def _finish_model(self, model, location=True):

        if location:
            location = self.location_url(model['path'])
            self.set_header('Location', location)
        self.set_header('Last-Modified', model['last_modified'])
        self.set_header('Content-Type', 'application/json')

        # print("---------> finish_model", model)

        self.finish(json.dumps(model))


class ShareHandle(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi()

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @web.authenticated
    @gen.coroutine
    def post(self):
        endpoint = self.get_json_body()['endpoint']
        file_id = self.get_json_body()['file_id']
        grantee = self.get_json_body()['grantee']
        idp = self.get_json_body()['idp']
        role = self.get_json_body()['role']
        grantee_type = self.get_json_body()['grantee_type']
        RequestHandler.handle_request(self, self.share_api.create, 201, endpoint, file_id, grantee, idp, role, grantee_type)

    @web.authenticated
    @gen.coroutine
    def delete(self):
        share_id = self.get_query_argument('share_id')
        RequestHandler.handle_request(self, self.share_api.remove, 204, share_id)

    def put(self):
        share_id = self.get_json_body()['share_id']
        role = self.get_json_body()['role']
        RequestHandler.handle_request(self, self.share_api.update, 204, share_id, role)


class ListSharesHandler(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi()

    @web.authenticated
    @gen.coroutine
    def get(self):
        RequestHandler.handle_request(self, self.share_api.list, 200)


class ListReceivedSharesHandler(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi()

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
        return Cs3ShareApi()

    @web.authenticated
    @gen.coroutine
    def get(self):
        print("Listing shares for file")
        file_id = self.get_query_argument('file_id', default=None)
        print("FILE_ID is " + file_id)
        RequestHandler.handle_request(self, self.share_api.list_grantees_for_file, 200, file_id)


class OcmShareHandle(APIHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @web.authenticated
    @gen.coroutine
    def get(self):
        output = {
            'ocm_share': 'hello OCM Share'
        }
        self.set_header('Content-Type', 'application/json')
        self.finish(json.dumps(output))


handlers = [
    (r"/api/cs3test/helloworld", HelloWorldHandle),
    (r"/api/cs3test/files", FilesHandle),
    (r"/api/cs3test/shares", ShareHandle),
    (r"/api/cs3test/shares/list", ListSharesHandler),
    (r"/api/cs3test/shares/received", ListReceivedSharesHandler),
    (r"/api/cs3test/shares/file", ListSharesForFile),
    (r"/api/cs3test/ocmshares", OcmShareHandle),
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
