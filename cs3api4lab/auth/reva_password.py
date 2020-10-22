import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.rpc.code_pb2 as cs3code
import time
from tornado import web

from cs3api4lab.auth.authenticator import Authenticator
from cs3api4lab.auth.channel_connector import ChannelConnector


class RevaPassword(Authenticator):
    cs3_stub = None
    tokens = {}

    def __init__(self, config=None, log=None):
        self.config = config
        self.log = log
        channel = ChannelConnector().get_channel()
        self.cs3_stub = cs3gw_grpc.GatewayAPIStub(channel)

    def authenticate(self, client_id):
        if client_id not in self.tokens or self.tokens[client_id]['exp'] < time.time():
            auth_req = cs3gw.AuthenticateRequest(type=self.config['login_type'],
                                                 client_id=self.config['client_id'],
                                                 client_secret=self.config['client_secret'])
            auth_res = self.cs3_stub.Authenticate(auth_req)

            if auth_res.status.code != cs3code.CODE_OK:
                if self.log is not None:
                    self.log.error('msg="Failed to authenticate" user="%s" code="%s"' % (client_id, auth_res.status.code))
                raise web.HTTPError(401, u'Failed to authenticate user: %s' % client_id, reason="unauthenticated")

            self.tokens[client_id] = {'tok': auth_res.token,
                                      'exp': time.time() + float(self.config['auth_token_validity'])}

        # piggy back on the opportunity to expire old tokens, but asynchronously
        # as to not impact the current session: let's use python3.7's coroutines support
        # asyncio.run(_async_cleanuptokens())

        return self.tokens[client_id]['tok']
