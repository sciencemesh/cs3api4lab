from datetime import datetime

from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager
from notebook.services.contents.manager import ContentsManager
from tornado import web

from cs3api4lab.cs3_file_api import Cs3FileApi
from notebook import _tz as tz
import mimetypes

class CS3APIsManager(ContentsManager):
    cs3_config_dir = ""
    cs3_config = {}
    cs3_user_id = "einstein"

    # ToDo: Change to cs3 Type
    TYPE_FILE = 1
    TYPE_DIRECTORY = 2

    log = None
    cs3_endpoint = None

    def __init__(self, parent, log):

        #
        # Get config from jupyter_cs3_config.json file
        #
        config_path = jupyter_config_path()
        if self.cs3_config_dir not in config_path:
            # add self.config_dir to the front, if set manually
            config_path.insert(0, self.cs3_config_dir)
        cm = ConfigManager(read_config_path=config_path)

        cs3_config = cm.get('jupyter_cs3_config')

        self.cs3_config = cs3_config.get("cs3", {
            "revahost": "127.0.0.1:19000",
            "endpoint": "/",
            "authtokenvalidity": "3600",
            "chunksize": "4194304"
        })

        self.cs3_endpoint = self.cs3_config["endpoint"]
        self.log = log

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
        """Get a file, notebook or directory model."""

        path = self._normalize_path(path)

        if type in (None, 'directory') and self._is_dir(path):
            model = self._dir_model(path, content=content)
        elif type == 'notebook' or (type is None and path.endswith('.ipynb')):
            raise NotImplementedError('cs3: missing')
        else:
            if type == 'directory':
                raise web.HTTPError(400, u'%s is a directory' % path, reason='bad type')
            raise NotImplementedError('cs3: missing')

        return model

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

    

                    if type == 'notebook' or (type is None and path.endswith('.ipynb')):
                        contents.append(
                            self._convert_container_to_notebook_model(cs3_model, cs3_container)
                        )
                    else:
                        contents.append(
                            self._convert_container_to_file_model(cs3_model, cs3_container)
                        )
                else:

                    self.log.error(u'Unexpected type: %s %s', cs3_model.path, cs3_model.type)
                    raise web.HTTPError(500, u'Unexpected type: %s %s' % (cs3_model.path, cs3_model.type))

        return model

    def _convert_container_to_file_model(self, cs3_model, cs3_container):

        model = self._convert_container_to_base_model(cs3_model.path, cs3_container)
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(cs3_model.path)[0]

        return model

    def _convert_container_to_notebook_model(self, cs3_model, cs3_container):

        model = self._convert_container_to_base_model(cs3_model.path, cs3_container)
        model['type'] = 'notebook'
        model['mimetype'] = mimetypes.guess_type(cs3_model.path)[0]

        return model
