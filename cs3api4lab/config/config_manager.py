import os
from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager
from traitlets.config import LoggingConfigurable


class Cs3ConfigManager(LoggingConfigurable):
    __config = None
    __config_dir = "\\jupyter-config"
    __config_file_name = 'jupyter_cs3_config'

    @classmethod
    def get_config(cls):
        if not cls.__config:
            cls._create_config()
        return cls.__config

    @classmethod
    def _create_config(cls):
        #
        # Get config from jupyter_cs3_config.json file
        #
        config_path = jupyter_config_path()
        if cls.__config_dir not in config_path:
            # add self.config_dir to the front, if set manually
            config_path.insert(0, os.getcwd() + cls.__config_dir)
        cm = ConfigManager(read_config_path=config_path)

        config_file = cm.get(cls.__config_file_name)
        cls.__config = config_file.get("cs3")

        if cls.__config is None:
            cls.log.error(f'Error while reading cs3 config file {cls.__config_dir}{cls.__config_file_name}')
            raise IOError(u'Error while reading cs3 config file')
        #
        # Overwriting configuration values with environment variables
        #
        env_names = {"reva_host", "client_id", "client_secret", "home_dir"}
        for name in env_names:
            env_name = "CS3_" + name.upper()
            if env_name in os.environ:
                cls.log.debug(f"Overwriting config value {name}")
                cls.__config[name] = os.environ[env_name]
