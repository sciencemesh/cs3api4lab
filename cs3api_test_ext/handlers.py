from typing import Optional, Awaitable

from notebook.base.handlers import APIHandler
from tornado import gen, web
import json

from cs3api_test_ext import CS3APIsManager


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

        cs3manager = self.cs3api_manager
        output = {
            'files': 'files',
            'path': path,
            'format': format,
            'type': type,
            'model': cs3manager.get(path=path, type=type, format=format, content=content)
        }
        self.set_header('Content-Type', 'application/json')
        self.finish(json.dumps(output))

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


class ShareHandle(APIHandler):

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    @web.authenticated
    @gen.coroutine
    def get(self):
        output = {
            'share': 'hello share'
        }
        self.set_header('Content-Type', 'application/json')
        self.finish(json.dumps(output))


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
    (r"/api/cs3test/ocmshares", OcmShareHandle),
]