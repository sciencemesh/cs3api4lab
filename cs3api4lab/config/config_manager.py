import os
from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager
from traitlets.config import LoggingConfigurable


class Config(LoggingConfigurable):
    config = {
        "reva_host": "",
        "client_id": "",
        "client_secret": "",
        "auth_token_validity": "3600",
        "endpoint": "/",
        "home_dir": "/home",
        "chunk_size": "4194304",
        "secure_channel": False,
        "client_cert": "",
        "client_key": "",
        "ca_cert": "",
        "login_type": "basic"
    }
    __config_dir = "\\jupyter-config"
    __config_file_name = 'jupyter_cs3_config'


    def __init__(self):
        config_path = jupyter_config_path()
        if self.__config_dir not in config_path:
            # add self.config_dir to the front, if set manually
            config_path.insert(0, os.getcwd() + self.__config_dir)
        cm = ConfigManager(read_config_path=config_path)
        config_file = cm.get(self.__config_file_name)
        config = config_file.get("cs3")

        # overwriting default values with config file
        if config is not None:
            for key in self.config.keys():
                if key in config.keys() and config[key]:
                    self.config[key] = config[key]

        # overwriting the values with env vars
        for key in self.config.keys():
            env_name = "CS3_" + key.upper()
            if env_name in os.environ:
                self.config[key] = os.environ[env_name]

        if not self.config["reva_host"]:
            raise KeyError("Reva host not provided")
        if not self.config["client_id"]:
            raise KeyError("Client ID not provided")


class Cs3ConfigManager:
    __config_instance = None

    @classmethod
    def get_config(cls):
        if not cls.__config_instance:
            cls.__config_instance = Config()
        return cls.__config_instance.config
