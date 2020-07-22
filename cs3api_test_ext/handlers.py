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

        print("-------------------> FilesHandle::get():")
        print("path: ", path, "content: ", content, "type: ", type, "format: ", format)

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

        print("-------------------> FilesHandle::get():")

        self._finish_model(model)

    @web.authenticated
    @gen.coroutine
    def post(self, path=''):
        """
        Create a new file in the specified path.
        """

    @web.authenticated
    @gen.coroutine
    def put(self, path=''):
        """
        Saves the file in the location specified by name and path.
        """

    @web.authenticated
    @gen.coroutine
    def delete(self, path=''):
        """
        Delete a file in the given path
        """

    def _finish_model(self, model, location=True):

        if location:
            location = self.location_url(model['path'])
            self.set_header('Location', location)
        self.set_header('Last-Modified', model['last_modified'])
        self.set_header('Content-Type', 'application/json')

        # print("---------> finish_model", model)

        self.finish(json.dumps(model))


class ShareHandle(APIHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @web.authenticated
    @gen.coroutine
    def post(self, endpoint, fileid, userid, grantee, idp=None, role="viewer", grantee_type="user"):
        response = Cs3ShareApi.create(endpoint, fileid, userid, grantee, idp, role, grantee_type)
        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(json.dumps(response))

    @web.authenticated
    @gen.coroutine
    def delete(self, shareid, userid):
        response = Cs3ShareApi.remove(shareid, userid)
        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(json.dumps(response))

    def put(self, endpoint, shareid, userid, role="viewver"):
        response = Cs3ShareApi.update(endpoint, shareid, userid, role)
        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(json.dumps(response))


class ListSharesHandler(APIHandler):
    @web.authenticated
    @gen.coroutine
    def get(self, userid):
        response = Cs3ShareApi.list(userid=userid)
        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(json.dumps(response))


class ListReceivedSharesHandler(APIHandler):
    @web.authenticated
    @gen.coroutine
    def get(self, userid):
        response = Cs3ShareApi.list_received(userid=userid)
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
    (r"/api/cs3test/shares/list-received", ListReceivedSharesHandler),
    (r"/api/cs3test/ocmshares", OcmShareHandle),
]
