import importlib
from datetime import datetime

import jwt
from cs3api4lab.config.config_manager import Cs3ConfigManager
import cs3.rpc.v1beta1.code_pb2 as cs3code
from tornado import web

import cs3.gateway.v1beta1.gateway_api_pb2 as cs3gw
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
from cs3api4lab.auth.channel_connector import ChannelConnector


class Authenticator:
    token = None
    cs3_stub = None

    def __init__(self, config=None, log=None):
        self.config = config
        self.log = log
        self.channel = ChannelConnector().get_channel()
        self.cs3_stub = cs3gw_grpc.GatewayAPIStub(self.channel)

    """
    Parent class for different authentication types. Authentication class must implement the authenticate method.
    If authentication class can refresh token must implement the refresh token method.
    Using auth type is declared in the config file.
    """

    def authenticate(self):
        """
        The basic authenticate method, return IOP token or refresh if is not present or invalid.
        """
        if self.token is None or self._check_token(self.token) is False:
            self.refresh_token()

        return self.token

    def refresh_token(self):
        self.raise_401_error()

    def raise_401_error(self):
        if self.log is not None:
            self.log.error('msg="Failed to authenticate" user="%s"' % self.config['client_id'])
        raise web.HTTPError(401, u'Failed to authenticate user', reason="unauthenticated")

    def _auth_in_iop(self, client_secret_or_token, login_type="basic"):

        auth_req = cs3gw.AuthenticateRequest(type=login_type,
                                             client_id=self.config['client_id'],
                                             client_secret=client_secret_or_token)
        auth_res = self.cs3_stub.Authenticate(auth_req)

        if auth_res.status.code != cs3code.CODE_OK or self._check_token(auth_res.token) is False:
            self.raise_401_error()

        return auth_res.token

    def _check_token(self, token):
        decode = jwt.decode(jwt=token, verify=False)
        now = datetime.timestamp(datetime.now())
        if decode['exp'] is not None and now > decode['exp']:
            return False

        return True


class Auth: 
    __auth_instance = None

    @classmethod
    def get_authenticator(cls, config=None, log=None):

        if cls.__auth_instance is None:

            if config is None:
                config = Cs3ConfigManager().get_config()

            if log is not None:
                log.info(f"Authenticate with method {config['authenticator_class']}")

            class_name = config['authenticator_class'].split('.')[-1]
            module_name = config['authenticator_class'].split(class_name)[0]
            module_name = module_name.rstrip('.')

            if class_name == "Authenticator":
                raise AttributeError("Can't instantiate Authenticator class")

            module = importlib.import_module(module_name)
            clazz = getattr(module, class_name)
            cls.__auth_instance = clazz(config=config, log=log)

        return cls.__auth_instance

    @classmethod
    def clean(cls):
        cls.__auth_instance = None
