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
            model = self._file_model(path, content=content, format=format)

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

    def _cs3_file_api(self):
        return Cs3FileApi(self.cs3_config, self.log)

    def _normalize_path(self, path):

        if path[0] != '/':
            path = '/' + path
        return path

    def _get_parent_path(self, path):

        directories = path.rsplit('/')
        directories.reverse()
        parent_path = self._replace_last(str(path), directories[0])
        return parent_path

    def _replace_last(self, source_string, replace_what, replace_with=""):

        head, _sep, tail = source_string.rpartition(replace_what)
        return head + replace_with + tail

    def _read_file(self, path):

        content = ''
        for chunk in self._cs3_file_api().read_file(path, self.cs3_user_id, self.cs3_endpoint):
            content += chunk.decode('utf-8')

        return content

    def _dir_model(self, path, content):

        cs3_container = self._cs3_file_api().read_directory(path, self.cs3_user_id, self.cs3_endpoint)
        model = self._convert_container_to_directory_model(path, cs3_container, content)

        return model


    def _file_model(self, path, content, format):

        model, tmp_model = self._create_base_model_from_cs3_container(path)
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(tmp_model.path)[0]

        if content:
            content = self._read_file(tmp_model.path)

            if model['mimetype'] is None:
                default_mime = {
                    'text': 'text/plain',
                    'base64': 'application/octet-stream'
                }[format]
                model['mimetype'] = default_mime

            model.update(
                content=content,
                format=format,
            )

        return model

    def _is_dir(self, path):

        if path == '/' or path == '' or path is None:
            return True

        parent_path = self._get_parent_path(path)

        try:
            cs3_container = self._cs3_file_api().read_directory(parent_path, self.cs3_user_id, self.cs3_endpoint)
        except Exception as ex:
            self.log.error(u'Error while reading container: %s %s', path, ex, exc_info=True)
            raise web.HTTPError(500, u'Unexpected error while reading container: %s %s' % (path, ex))

        for cs3_model in cs3_container:

            if cs3_model.type == self.TYPE_FILE and cs3_model.path == path:
                return False
            if cs3_model.type == self.TYPE_DIRECTORY and cs3_model.path == path:
                return True

        return False

    def _create_base_model_from_cs3_container(self, path):

        parent_path = self._get_parent_path(path)

        cs3_file_api = self._cs3_file_api()
        cs3_container = cs3_file_api.read_directory(self.cs3_config['endpoint'], parent_path, self.cs3_user_id)

        cs3_model = None
        for cs3_tmp_model in cs3_container:
            if cs3_tmp_model.type == self.TYPE_FILE and cs3_tmp_model.path == path:
                cs3_model = cs3_tmp_model

        if cs3_model is None:
            raise web.HTTPError(404, u'%s is not a file' % path, reason='bad type')

        model = self._convert_container_to_base_model(cs3_model.path, cs3_container)
        return model, cs3_model

    def _convert_container_to_base_model(self, path, cs3_container):

        size = None
        writable = False
        created = datetime(1970, 1, 1, 0, 0, tzinfo=tz.UTC)
        last_modified = datetime(1970, 1, 1, 0, 0, tzinfo=tz.UTC)

        #
        # Get data from container element
        #
        for cs3_model in cs3_container:
            if cs3_model.path == path:
                size = cs3_model.size
                created = datetime.fromtimestamp(cs3_model.mtime.seconds, tz=tz.UTC)
                last_modified = datetime.fromtimestamp(cs3_model.mtime.seconds, tz=tz.UTC)

        # ToDo: Implement file writable permission from Riva
        # try:
        #     model['writable'] = os.access(os_path, os.W_OK)
        # except OSError:
        #     self.log.error("Failed to check write permissions on %s", os_path)
        #     model['writable'] = False

        #
        # Create the base model
        #
        model = {}
        model['name'] = path.rsplit('/', 1)[-1]
        model['path'] = path
        model['last_modified'] = last_modified
        model['created'] = created
        model['content'] = None
        model['format'] = None
        model['mimetype'] = None
        model['size'] = size
        model['writable'] = writable
        model['type'] = None

        return model

    def _convert_container_to_directory_model(self, path, cs3_container, content=True):

        model = self._convert_container_to_base_model(path, cs3_container)
        model['size'] = None
        model['type'] = 'directory'

        if content:
            model['content'] = contents = []
            model['format'] = 'json'

            for cs3_model in cs3_container:
                # ToDo: get data from cs3_model
                if cs3_model.type == self.TYPE_DIRECTORY:
                    sub_model = self._convert_container_to_base_model(cs3_model.path, cs3_container)
                    sub_model['size'] = None
                    sub_model['type'] = 'directory'
                    contents.append(sub_model)

                elif cs3_model.type == self.TYPE_FILE:

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
