import configparser
import os
from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager


class Cs3ConfigManager:
    config = {}
    config_dir = "\\jupyter-config"
    config_file_name = 'jupyter_cs3_config'

    def __init__(self, log, directory=None):
        #
        # Get config from jupyter_cs3_config.json file
        #
        self.log = log

        if directory is not None:
            self.config_dir = directory

        config_path = jupyter_config_path()
        if self.config_dir not in config_path:
            # add self.config_dir to the front, if set manually
            config_path.insert(0, os.getcwd() + self.config_dir)
        cm = ConfigManager(read_config_path=config_path)

        config_file = cm.get(self.config_file_name)
        self.config = config_file.get("cs3")

        if self.config is None:
            log.error(f'Error while reading cs3 config file {self.config_dir}{self.config_file_name}')
            raise IOError(u'Error while reading cs3 config file')
        #
        # Overwriting configuration values with environment variables
        #
        env_names = {"reva_host", "client_id", "client_secret", "home_dir"}
        for name in env_names:
            env_name = "CS3_" + name.upper()
            if env_name in os.environ:
                log.debug(f"Overwriting config value {name}")
                self.config[name] = os.environ[env_name]
