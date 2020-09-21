import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import time
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
from cs3api_test_ext.config.config_manager import Cs3ConfigManager
from cs3api_test_ext.auth.channel_connector import ChannelConnector


class Authenticator:
    tokens = {}  # map client_id [string] to {authentication token, token expiration time}

    def __init__(self):
        self.config = Cs3ConfigManager().config
        channel = ChannelConnector().channel
        self.cs3_stub = cs3gw_grpc.GatewayAPIStub(channel)

    def authenticate(self, client_id):
        # ToDo: use real authentication data or get token from author provider
        # authReq = cs3gw.AuthenticateRequest(type='bearer', client_secret=userid)

        if client_id not in self.tokens or self.tokens[client_id]['exp'] < time.time():
            auth_req = cs3gw.AuthenticateRequest(type=self.config['login_type'],
                                                 client_id=self.config['client_id'],
                                                 client_secret=self.config['client_secret'])
            auth_res = self.cs3_stub.Authenticate(auth_req)
            self.tokens[client_id] = {'tok': auth_res.token,
                                    'exp': time.time() + float(self.config['auth_token_validity'])}

        # piggy back on the opportunity to expire old tokens, but asynchronously
        # as to not impact the current session: let's use python3.7's coroutines support
        # asyncio.run(_async_cleanuptokens())

        return self.tokens[client_id]['tok']
