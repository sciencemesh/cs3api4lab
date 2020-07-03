import configparser
import logging

from notebook.services.contents.manager import ContentsManager
from cs3api_test_ext.cs3api.cs3_file_api import Cs3FileApi


class CS3APIsManager(ContentsManager):

    def __cs3_file_api(self):

        # ToDo: Setup logger from jupyter logger

        log_handler = logging.FileHandler('/var/tmp/cs3api.log')
        log_handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(name)s[%(process)d] %(levelname)-8s %(message)s',
                                                   datefmt='%Y-%m-%dT%H:%M:%S'))
        log = logging.getLogger('cs3api.test')
        log.addHandler(log_handler)
        log.setLevel(logging.DEBUG)

        config = configparser.ConfigParser()

        # ToDo: Setup config from jupyter config

        # try:
        #     with open('test.conf') as fdconf:
        #         config.read_file(fdconf)
        #     self.userid = config.get('cs3', 'userid')
        #     self.endpoint = config.get('cs3', 'endpoint')
        # except (KeyError, configparser.NoOptionError):
        #     print("Missing option or missing configuration, check the test.conf file")
        #     raise

        self.storage = Cs3FileApi(config, log)

        return Cs3FileApi(self, config, log)

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

        # ToDo: get user info/token from jupyter session
        return self.__cs3_file_api().read_file("", path, "einstein")

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



