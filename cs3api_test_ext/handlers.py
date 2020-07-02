from typing import Optional, Awaitable

from notebook.base.handlers import APIHandler
from tornado import gen, web
import json

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

    @web.authenticated
    @gen.coroutine
    def get(self):
        output = {
            'files': 'files'
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
