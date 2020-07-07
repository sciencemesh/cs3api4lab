import logging

from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager
from notebook.services.contents.manager import ContentsManager

from cs3api_test_ext.cs3_file_api import Cs3FileApi


class CS3APIsManager(ContentsManager):

    config_dir = ""
    config = {}

    def __init__(self):

        #
        # Get config from jupyter_cs3_config.json file
        #
        config_path = jupyter_config_path()
        if self.config_dir not in config_path:
            # add self.config_dir to the front, if set manually
            config_path.insert(0, self.config_dir)
        cm = ConfigManager(read_config_path=config_path)

        cs3_config = cm.get('jupyter_cs3_config')

        self.config = cs3_config.get("cs3", {
            "revahost": "127.0.0.1:19000",
            "endpoint": "/",
            "authtokenvalidity": "3600",
            "chunksize": "4194304"
        })

        return

    def __cs3_file_api__(self):

        #
        # ToDo: Setup logger from jupyter logger
        #

        log_handler = logging.FileHandler('/var/tmp/cs3api.log')
        log_handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(name)s[%(process)d] %(levelname)-8s %(message)s',
                                                   datefmt='%Y-%m-%dT%H:%M:%S'))
        log = logging.getLogger('cs3api.test')
        log.addHandler(log_handler)
        log.setLevel(logging.DEBUG)


        return Cs3FileApi(self.config, log)

    def dir_exists(self, path):
        """Does a directory exist at the given path?
        Like os.path.isdir
        Override this method in subclasses.
        Parameters
        ----------
        path : string
            The path to check
        Returns
        -------
        exists : bool
            Whether the path does indeed exist.
        """
        raise NotImplementedError('cs3: missing')

    def is_hidden(self, path):
        """Is path a hidden directory or file?
        Parameters
        ----------
        path : string
            The path to check. This is an API path (`/` separated,
            relative to root dir).
        Returns
        -------
        hidden : bool
            Whether the path is hidden.
        """
        raise NotImplementedError('cs3: missing')

    def file_exists(self, path=''):
        """Does a file exist at the given path?
        Like os.path.isfile
        Override this method in subclasses.
        Parameters
        ----------
        path : string
            The API path of a file to check for.
        Returns
        -------
        exists : bool
            Whether the file exists.
        """
        raise NotImplementedError('cs3: missing')

    def get(self, path, content=True, type=None, format=None):
        """Get a file or directory model."""

        # ToDo: Reorganize file or directory type

        # ToDo: get user info/token from jupyter session
        content = ''
        for chunk in self.__cs3_file_api__().read_file("", path, "einstein"):
            if len(chunk) > 0:
                content += chunk.decode('utf-8')

        return content

    def save(self, model, path):
        """
        Save a file or directory model to path.
        Should return the saved model with no content.  Save implementations
        should call self.run_pre_save_hook(model=model, path=path) prior to
        writing any data.
        """
        raise NotImplementedError('cs3: missing')

    def delete_file(self, path):
        """Delete the file or directory at path."""
        raise NotImplementedError('cs3: missing')

    def rename_file(self, old_path, new_path):
        """Rename a file or directory."""
        raise NotImplementedError('cs3: missing')



