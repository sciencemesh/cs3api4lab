import os
from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager
from traitlets.config import LoggingConfigurable


class Config(LoggingConfigurable):
    config = {
        "auth_token_validity": "3600",
        "endpoint": "/",
        "home_dir": "/home",
        "root_dir_list": "/home,/reva", # List of root dirs. Example: Exaple config "/home,/reva" for storage-references: https://developer.sciencemesh.io/docs/iop/deployment/kubernetes/providers/
        "chunk_size": "4194304",
        "secure_channel": True,
        "authenticator_class": "cs3api4lab.auth.RevaPassword",
        "login_type": "basic",
        "locks_expiration_time": 150,
        "client_key": None,
        "client_cert": None,
        "ca_cert": None,
        "tus_enabled": False,
        "enable_ocm": False,
        "shared_folder": "MyShares"
    }
    __config_dir = "jupyter-config"
    __config_file_name = 'jupyter_cs3_config'


    def __init__(self):
        config_path = jupyter_config_path()
        if self.__config_dir not in config_path:
            # add self.config_dir to the front, if set manually
            config_path.insert(0, os.path.join(os.getcwd(), self.__config_dir)) #might be os.path.join(os.getcwd(), 'cs3api4lab', self.__config_dir) depending on the environment setup"
        cm = ConfigManager(read_config_path=config_path)
        config_file = cm.get(self.__config_file_name)
        config = config_file.get("cs3", {})

        self.config = self.config | config

        # overwriting the values with env vars
        env_vars = {env[4:].lower():os.environ[env] for env in os.environ if env.startswith("CS3_")}
        self.config = self.config | env_vars

        if len(self.config["root_dir_list"]) > 0:
            root_dir_list = tuple(dir.strip() for dir in self.config["root_dir_list"].split(','))
            self.config["root_dir_list"] = root_dir_list
        else:
            self.config["root_dir_list"] = tuple()

        if not self.config["reva_host"]:
            raise KeyError("Reva host not provided")
        if not self.config["client_id"]:
            raise KeyError("Client ID not provided")

        self.log.debug(f"Provided configuraton: {self.config}")


class Cs3ConfigManager:
    __config_instance = None

    @classmethod
    def get_config(cls):
        if not cls.__config_instance:
            cls.__config_instance = Config()
        return cls.__config_instance.config
