import importlib
from datetime import datetime

import jwt

from cs3api4lab.config.config_manager import Cs3ConfigManager


class Authenticator:
    """
    Parent class for different authentication types. Authentication class must implement the authenticate method.
    If authentication class can refresh token must implement the refresh token method.
    Using auth type is declared in the config file.
    """
    def authenticate(self, client_id):
        raise NotImplementedError("Not Implemented")

    def refresh_token(self, refresh_token=None):
        pass

    def check_token(self, token):
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
