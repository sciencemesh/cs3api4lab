from notebook.base.handlers import APIHandler
from tornado import gen, web
import json

class HelloWorldHandle(APIHandler):

    @web.authenticated
    @gen.coroutine
    def get(self):
        output = {
            'hello': 'world'
        }
        self.set_header('Content-Type', 'application/json')
        self.finish(json.dumps(output))

handlers = [(r"/api/cs3test/helloworld", HelloWorldHandle)]