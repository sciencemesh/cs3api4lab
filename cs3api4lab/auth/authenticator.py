import importlib
from datetime import datetime

import jwt

from cs3api4lab.config.config_manager import Cs3ConfigManager


class Authenticator:
    instance = None
    config = None

    def __init__(self, config=None, log=None):

        if config is None:
            config = Cs3ConfigManager().get_config()
        self.config = config

        if self.instance is None:

            if log is not None:
                log.info(f"Authenticate with method {self.config['authenticator_class']}")

            class_name = self.config['authenticator_class'].split('.')[-1]
            module_name = self.config['authenticator_class'].split(class_name)[0]
            module_name = module_name.rstrip('.')

            if class_name == "Authenticator":
                raise AttributeError("Can't instance Authenticator class")

            module = importlib.import_module(module_name)
            clazz = getattr(module, class_name)
            self.instance = clazz(config=self.config, log=log)

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
