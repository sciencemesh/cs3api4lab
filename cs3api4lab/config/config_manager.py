import os
import distutils.util as utils
from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager
from traitlets.config import LoggingConfigurable


class Config(LoggingConfigurable):
    config = None
    __config_dir = "\\jupyter-config"
    __config_file_name = 'jupyter_cs3_config'
    __env_names = {"reva_host",
                   "auth_token_validity",
                   "endpoint",
                   "home_dir",
                   "chunk_size",
                   "secure_channel",
                   "client_cert",
                   "client_key",
                   "ca_cert",
                   "client_id",
                   "client_secret",
                   "login_type"}

    def __init__(self):
        #
        # Get config from the env variables or from jupyter_cs3_config.json file
        #
        if 'CS3_EXT_CONFIG' in os.environ.keys() and utils.strtobool(os.environ['CS3_EXT_CONFIG']):
            self.config = {}
            self.log.info("Reading CS3 config from environment")
            for name in self.__env_names:
                env_name = "CS3_" + name.upper()
                if env_name in os.environ:
                    self.log.info(f"Reading config value {name} = " + str(os.environ[env_name]))
                    self.config[name] = os.environ[env_name]
                else:
                    self.log.error(f"Unable to read {name}")
                    raise ValueError(f"Unable to read {name} from environment variables")
        else:
            self.log.info(f'Reading CS3 config from file {self.__config_dir}{self.__config_file_name}')
            config_path = jupyter_config_path()
            if self.__config_dir not in config_path:
                # add self.config_dir to the front, if set manually
                config_path.insert(0, os.getcwd() + self.__config_dir)
            cm = ConfigManager(read_config_path=config_path)
            config_file = cm.get(self.__config_file_name)
            self.config = config_file.get("cs3")
            if self.config is None:
                self.log.error(f'Error while reading cs3 config file {self.__config_dir}{self.__config_file_name}')
                raise IOError(u'Error while reading cs3 config file')


class Cs3ConfigManager:
    __config_instance = None

    @classmethod
    def get_config(cls):
        if not cls.__config_instance:
            cls.__config_instance = Config()
        return cls.__config_instance.config

