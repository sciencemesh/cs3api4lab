from typing import Optional, Awaitable

from notebook.base.handlers import APIHandler
from notebook.utils import maybe_future
from tornado import gen, web
import json

from cs3api_test_ext import CS3APIsManager
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
        endpoint = self.get_query_argument('endpoint')
        file_id = self.get_query_argument('file_id')
        grantee = self.get_query_argument('grantee')
        idp = self.get_query_argument('idp')
        role = self.get_query_argument('role')
        grantee_type = self.get_query_argument('grantee_type')
        try:
            response = self.share_api.create(endpoint, file_id, grantee, idp, role, grantee_type)
        except Exception as err:
            self.set_status(500)
            self.finish(json.dumps(str(err)))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps(response))

    @web.authenticated
    @gen.coroutine
    def delete(self):
        share_id = self.get_query_argument('share_id')
        try:
            self.share_api.remove(share_id)
        except Exception as err:
            self.set_status(500)
            self.finish(json.dumps(err))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish()

    def put(self):
        share_id = self.get_query_argument('share_id')
        role = self.get_query_argument('role')
        try:
            self.share_api.update(share_id, role)
        except Exception as err:
            self.set_status(500)
            self.finish(json.dumps(err))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish()


class ListSharesHandler(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi()

    @web.authenticated
    @gen.coroutine
    def get(self):
        try:
            response = self.share_api.list()
        except Exception as err:
            self.set_status(500)
            self.finish(json.dumps(err))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps(response))


class ListReceivedSharesHandler(APIHandler):
    @property
    def share_api(self):
        return Cs3ShareApi()

    @web.authenticated
    @gen.coroutine
    def get(self):
        try:
            response = self.share_api.list_received()
        except Exception as err:
            self.set_status(500)
            self.finish(json.dumps(err))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps(response))

    @web.authenticated
    @gen.coroutine
    def put(self):
        share_id = self.get_query_argument('share_id', default=None)
        state = self.get_query_argument('state', default='pending')
        try:
            self.share_api.update_received(share_id, state)
        except Exception as err:
            self.set_status(500)
            self.finish(json.dumps(err))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish()


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
        try:
            response = self.share_api.list_grantees_for_file(file_id)
        except Exception as err:
            self.set_status(500)
            self.finish(json.dumps(err))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps(response))


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

# todo inheritance
# class HandlerUtil(APIHandler):
#
#     def handle_error(self, err):
#         self.set_status(500)
#         self.finish(json.dumps(err))
#
#     def handle_response(self, response):
#         self.set_header('Content-Type', 'application/json')
#         self.set_status(200)
#         if(response is None):
#             self.finish()
#         else:
#             self.finish(json.dumps(response))