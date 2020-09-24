import os
from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager
from traitlets.config import LoggingConfigurable


class Cs3ConfigManager(LoggingConfigurable):
    config = None
    __config_dir = "\\jupyter-config"
    __config_file_name = 'jupyter_cs3_config'

    def __new__(cls, *args, **kwargs):
        if cls.config is None:
            cls.config = super(Cs3ConfigManager, cls).__new__(cls)
        return cls.config

    def __init__(self):
        #
        # Get config from jupyter_cs3_config.json file
        #
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
        #
        # Overwriting configuration values with environment variables
        #
        env_names = {"reva_host", "client_id", "client_secret", "home_dir"}
        for name in env_names:
            env_name = "CS3_" + name.upper()
            if env_name in os.environ:
                self.log.debug(f"Overwriting config value {name}")
                self.config[name] = os.environ[env_name]
