import logging
import mimetypes
import os
from datetime import date, datetime
from pathlib import Path

from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager
from notebook.services.contents.manager import ContentsManager
from tornado import web
from notebook import _tz as tz

import nbformat

from cs3api_test_ext.cs3_file_api import Cs3FileApi


class CS3APIsManager(ContentsManager):

    cs3_config_dir = ""
    cs3_config = {}
    cs3_user_id = "einstein"

    # ToDo: Change to cs3 Type
    TYPE_FILE = 1
    TYPE_DIRECTORY = 2

    def __init__(self, parent, log):

        # print("->>>>>>>>>>>>>> CS3APIsManager __init__")
        # print(self, parent, log)

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

        return

    def _cs3_file_api(self):

        #
        # ToDo: Setup logger from jupyter logger
        #

        log_handler = logging.FileHandler('/var/tmp/cs3api.log')
        log_handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(name)s[%(process)d] %(levelname)-8s %(message)s',
                                                   datefmt='%Y-%m-%dT%H:%M:%S'))
        log = logging.getLogger('cs3api.test')
        log.addHandler(log_handler)
        log.setLevel(logging.DEBUG)


        return Cs3FileApi(self.cs3_config, log)

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

        # print("---> CS3APIsManager::get(): ", "path:", path, "content:", content, "type:", type, "format:", format)

        #
        # ToDo: Get user info/token from jupyter session
        #
        if type in (None, 'directory') and self._is_dir(path):
            model = self._dir_model(path, content=content)
        elif type == 'notebook' or (type is None and path.endswith('.ipynb')):
            model = self._notebook_model(path, content=content)
        else:
            if type == 'directory':
                raise web.HTTPError(400, u'%s is a directory' % path, reason='bad type')

            model = self._file_model(path, content=content, format=format)

        # print("---> CS3APIsManager::get(): ")

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

    def _dir_model(self, path, content):

        # print("---> FileContentsManager::_dir_model(): ", "path: ", path, "content: ", content)

        cs3_file_api = self._cs3_file_api()
        cs3_container = cs3_file_api.read_directory(self.cs3_config['endpoint'], path, self.cs3_user_id)
        model = self._convert_container_to_directory_model(path, cs3_container, content)

        # print("---> FileContentsManager::_dir_model(): ", model)

        return model

    def _notebook_model(self, path, content):

        model, tmp_model = self._create_base_model_from_cs3_container(path)
        model['type'] = 'notebook'

        if content:
            file_content = self._read_file(tmp_model.path, format)
            nb = nbformat.reads(file_content, as_version=4)
            self.mark_trusted_cells(nb, path)
            model['content'] = nb
            model['format'] = 'json'
            self.validate_notebook_model(model)

        # print("---> FileContentsManager::_notebook_model(): ", "model: ", model)

        return model

    def _file_model(self, path, content, format):

        model, tmp_model = self._create_base_model_from_cs3_container(path)
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(tmp_model.path)[0]

        if content:
            content = self._read_file(tmp_model.path, format)

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

        # print("---> FileContentsManager::_file_model(): ", "model:", model)

        return model

    def _convert_container_to_base_model(self, path, cs3_container):

        # print("---> FileContentsManager::_convert_container_to_base_model(): ", "path:", path)

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

        """
        ------------------------------------------------
        type: RESOURCE_TYPE_CONTAINER
        id {
          storage_id: "123e4567-e89b-12d3-a456-426655440000"
          opaque_id: "fileid-%2Fhome%2FMyShares"
        }
        etag: "\"56fb030b7dc4dfbf9e87fc4ed1ddb14d\""
        mime_type: "httpd/unix-directory"
        mtime {
          seconds: 1593606956
        }
        path: "/home/MyShares"
        permission_set {
          create_container: true
          list_container: true
        }
        size: 512
        owner {
          idp: "http://cernbox.cern.ch"
          opaque_id: "4c510ada-c86b-4815-8820-42cdf82c3d51"
        }
        arbitrary_metadata {
        }

        ------------------------------------------------

        ------------------------------------------------
        type: RESOURCE_TYPE_FILE
        id {
          storage_id: "123e4567-e89b-12d3-a456-426655440000"
          opaque_id: "fileid-%2Fnote1.txt"
        }
        etag: "\"94847abca98c9b8c2f8620c1b4566ecf\""
        mime_type: "text/plain; charset=utf-8"
        mtime {
          seconds: 1594107922
        }
        path: "/note1.txt"
        permission_set {
          create_container: true
          list_container: true
        }
        size: 637
        owner {
          idp: "http://cernbox.cern.ch"
          opaque_id: "4c510ada-c86b-4815-8820-42cdf82c3d51"
        }
        arbitrary_metadata {
        }

        ------------------------------------------------

        """

        # print("---> FileContentsManager::_convert_container_to_directory_model(): ", path)

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
                            self._convert_container_to_notebook_model(cs3_model, cs3_container, content=content)
                        )
                    else:
                        contents.append(
                            self._convert_container_to_file_model(cs3_model, cs3_container, content=content, format=format)
                        )
                else:
                    print("-> UNKNOWN TYPE: ", cs3_model.path, cs3_model.type)

        return model

    def _convert_container_to_file_model(self, cs3_model, cs3_container, content, format):

        model = self._convert_container_to_base_model(cs3_model.path, cs3_container)
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(cs3_model.path)[0]

        return model

    def _convert_container_to_notebook_model(self, cs3_model, cs3_container, content=True):

        model = self._convert_container_to_base_model(cs3_model.path, cs3_container)
        model['type'] = 'notebook'
        model['mimetype'] = mimetypes.guess_type(cs3_model.path)[0]

        return model

    def _is_dir(self, path):

        if path == '/' or path == '' or path is None:
            return True

        cs3_file_api = self._cs3_file_api()
        cs3_container = cs3_file_api.read_directory(self.cs3_config['endpoint'], path, self.cs3_user_id)

        for cs3_model in cs3_container:
            if cs3_model.type == self.TYPE_FILE and cs3_model.path == path:
                # print("IS_FILE: ", cs3_model.type, cs3_model.path)
                return False

        return True

    def _read_file(self, path, format):

        content = ''
        for chunk in self._cs3_file_api().read_file(self.cs3_config['endpoint'], path, self.cs3_user_id):
            content += chunk.decode('utf-8')

        return content

    def _replace_last(self, source_string, replace_what, replace_with=""):
        head, _sep, tail = source_string.rpartition(replace_what)
        return head + replace_with + tail

    def _create_base_model_from_cs3_container(self, path):

        directories = path.rsplit('/')
        directories.reverse()
        parent_path = self._replace_last(str(path), directories[0])

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