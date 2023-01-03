import nbformat
import os
import posixpath
import nest_asyncio

import cs3.storage.provider.v1beta1.resources_pb2 as resource_types
import cs3.rpc.v1beta1.code_pb2 as cs3code

from base64 import decodebytes
from jupyter_server.services.contents.manager import ContentsManager
from requests import HTTPError

from cs3api4lab.common.strings import Role
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from tornado import web
from nbformat.v4 import new_notebook
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.utils.share_utils import ShareUtils
from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.api.share_api_facade import ShareAPIFacade
from cs3api4lab.utils.model_utils import ModelUtils
from cs3api4lab.utils.asyncify import asyncify
from cs3api4lab.api.storage_api import StorageApi
from cs3api4lab.locks.factory import LockApiFactory
from cs3api4lab.exception.exceptions import ResourceNotFoundError
from traitlets.config import HasTraits

"""
This class redefines default upstream ContentsManager.
It's used for operations on files (user filesystem and files shared by users)

Note: This uses validation from ContentsManager package which means we are 
bound to the endpoint rules defined in ContentsManager.
"""
class CS3APIsManager(ContentsManager):
    cs3_config = None
    log = None
    file_api = None

    def __init__(self, parent, log, **kwargs):
        super().__init__(**kwargs)
        HasTraits.__init__(self, **kwargs)
        self.cs3_config = Cs3ConfigManager.get_config()
        self.log = log
        self.file_api = Cs3FileApi(self.log)
        self.share_api = ShareAPIFacade(log)
        self.storage_api = StorageApi(log)
        self.lock_api = LockApiFactory.create(log, self.cs3_config)

        #line below must be run in order for loop.run_until_complete() to work
        nest_asyncio.apply()

    # _is_dir is already async, so no need to asyncify this
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
        path = FileUtils.normalize_path(path)
        return self._is_dir(path)

    @asyncify
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
        path = FileUtils.normalize_path(path)
        parts = path.split('/')
        if any(part.startswith('.') for part in parts):
            return True
        return False

    @asyncify
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
        path = FileUtils.normalize_path(path)
        try:
            file_info = self.file_api.stat_info(path, self.cs3_config.endpoint)
        except FileNotFoundError:
            return False

        if file_info['type'] == resource_types.RESOURCE_TYPE_FILE:
            return True

        return False

    # can't be async because SQLite (used for jupyter notebooks) doesn't allow multithreaded operations by default
    def get(self, path, content=True, type=None, format=None):
        """Get a file, notebook or directory model."""
        path = FileUtils.normalize_path(path)
        model = None

        if type:
            if type == 'directory' and self._is_dir(path):
                model = self._dir_model(path, content=content)
            elif type == 'file' and self.file_exists(path):
                model = self._file_model(path, content=content, format=format)
            elif type == 'notebook' or (type is None and path.endswith('.ipynb')):
                try:   #this needs to be fixed/refactored in a separate issue
                    model = self._notebook_model(path, content=content)
                except Exception:
                    self.log.info("Notebook does not exist %s", path)
        else:
            if path.endswith('.ipynb'):
                try:   #this needs to be fixed/refactored in a separate issue
                    model = self._notebook_model(path, content=content)
                except Exception:
                    self.log.info("Notebook does not exist %s", path)
            elif self.file_exists(path):
                model = self._file_model(path, content=content, format=format)
            elif self._is_dir(path):
                model = self._dir_model(path, content=content)

        if model:
            return model

        raise web.HTTPError(404, u'Resource %s does not exist' % path)

    @asyncify
    def get_kernel_path(self, path, model=None):
        """
        Return the initial API path of a kernel associated with a given notebook.
        Since the kernel only uses the access to the local storage (where we assume we 
        fuse mount the remote storage), we need to translate the web (cs3api based) paths, 
        to a local one.

        WARNING: root_dir will be later added to kernel_path, so consider it when defining kernel_path
        """
        self.log.debug(f"Requesting the kernel path for {path}")

        # FIXME delete this everywhere
        if ":" in path:
            path = path.split(":")[1]

        kernel_path = self.cs3_config.kernel_path
        path = posixpath.join(kernel_path, path)

        # Lets use the local filesystem instead of going via cs3apis
        if os.path.isdir(path):
            return path
        if '/' in path:
            parent_dir = path.rsplit('/', 1)[0]
        else:
            parent_dir = ''
        return parent_dir

    # can't be async because SQLite (used for jupyter notebooks) doesn't allow multithreaded operations by default
    def save(self, model, path):
        """
        Save a file or directory model to path.
        Should return the saved model with no content.  Save implementations
        should call self.run_pre_save_hook(model=model, path=path) prior to
        writing any data.
        """
        path = FileUtils.check_and_transform_file_path(path)
        # self._check_write_permissions(path)

        if 'type' not in model:
            raise web.HTTPError(400, u'No file type provided')
        if 'content' not in model and model['type'] != 'directory':
            raise web.HTTPError(400, u'No file content provided')
        self.log.debug("Saving %s", path)
        # ToDo: Implements run_pre_save_hook and run_post_save_hook
        # self.run_pre_save_hook(model=model, path=path)

        try:
            if model['type'] == 'notebook':

                nb = nbformat.from_dict(model['content'])
                self.check_and_sign(nb, path)
                self._save_notebook(path, nb, model['format'])

                # ToDo: Implement save to checkpoint
                # if not self.checkpoints.list_checkpoints(path):
                #     self.create_checkpoint(path)

            elif model['type'] == 'file':
                self._save_file(path, model['content'], model['format'])

            elif model['type'] == 'directory':
                self._save_directory(path)

            else:
                raise web.HTTPError(400, "Unhandled contents type: %s" % model['type'])

        except web.HTTPError:
            raise

        except Exception as e:
            self.log.error(u'Error while saving file: %s %s', path, e, exc_info=True)
            raise web.HTTPError(500, u'Unexpected error while saving file: %s %s' % (path, e))

        validation_message = None

        if model['type'] == 'notebook':
            self.validate_notebook_model(model)
            validation_message = model.get('message', None)
            model = self._notebook_model(path, content=False)

        elif model['type'] == 'file':
            model = self._file_model(path, content=False, format=None)
        elif model['type'] == 'directory':
            model = self._dir_model(path, content=False)
        if validation_message:
            model['message'] = validation_message

        # self.run_post_save_hook(model=model, os_path=path)

        return model

    @asyncify
    def delete_file(self, path):
        """Delete the file or directory at path."""
        path = FileUtils.normalize_path(path)
        try:
            self.file_api.remove(path, self.cs3_config.endpoint)

        except FileNotFoundError as e:
            self.log.error(u'File not found error: %s %s', path, e, exc_info=True)
            raise web.HTTPError(404, u'No such file or directory: %s %s' % (path, e))

        except Exception as e:
            self.log.error(u'Unknown error delete file: %s %s', path, e, exc_info=True)
            raise web.HTTPError(500, u'Unknown error delete file: %s %s' % (path, e))

    @asyncify
    def rename_file(self, old_path, new_path):
        """Rename a file or directory."""

        if new_path == old_path:
            return

        #
        # ToDo: Implements validate file like: notebook/services/contents/filemanager.py:587 using Reva API
        #
        old_path = FileUtils.normalize_path(old_path)
        new_path = FileUtils.normalize_path(new_path)

        try:
            self.file_api.move(old_path, new_path, self.cs3_config.endpoint)
        except Exception as e:
            self.log.error(u'Error renaming file: %s %s', old_path, e)
            raise web.HTTPError(500, u'Error renaming file: %s %s' % (old_path, e))

    # can't be async because SQLite (used for jupyter notebooks) doesn't allow multithreaded operations by default
    def new(self, model=None, path=''):

        path = path.strip('/')
        path = FileUtils.normalize_path(path)
        # self._check_write_permissions(path)

        if model is None:
            model = {}

        if path.endswith('.ipynb'):
            model.setdefault('type', 'notebook')
        else:
            model.setdefault('type', 'file')

        # no content, not a directory, so fill out new-file model
        if 'content' not in model and model['type'] != 'directory':
            if model['type'] == 'notebook':
                model['content'] = new_notebook()
                model['format'] = 'json'
            else:
                model['content'] = ''
                model['type'] = 'file'
                model['format'] = 'text'

        model = self.save(model, path)

        return model

    def _get_parent_path(self, path):

        directories = path.rsplit('/')
        directories.reverse()

        if directories[0] != '':
            path = self._replace_last(str(path), directories[0])

        return FileUtils.normalize_path(path)

    def _replace_last(self, source_string, replace_what, replace_with=""):
        head, _sep, tail = source_string.rpartition(replace_what)
        return head + replace_with + tail

    def _read_file(self, stat, file_format=None):
        if file_format is None or file_format == "text":
            try:
                content = ''
                for chunk in self.file_api.read_file(stat, self.cs3_config.endpoint):
                    content += chunk.decode('utf-8')

                return content
            except UnicodeError as e:
                if file_format == "text":
                    raise HTTPError(
                        400,
                        "%s is not UTF-8 encoded" % stat['filepath'],
                        reason="bad format",
                    ) from e

        content = []
        for chunk in self.file_api.read_file(stat, self.cs3_config.endpoint):
            content.append(chunk)

        return b''.join(content)

    @asyncify
    def _dir_model(self, path, content):
        try:
            cs3_container = self.file_api.read_directory(path, self.cs3_config.endpoint)
            model = ModelUtils.convert_container_to_directory_model(path, cs3_container, content)
        except ResourceNotFoundError:
            raise web.HTTPError(404, u'%s does not exist' % path)
        return model

    @asyncify
    def _file_model(self, path, content, format):
        file_info = None
        model = ModelUtils.create_empty_file_model(path)
        try:
            file_info = self.file_api.stat_info(path, self.cs3_config.endpoint)
        except Exception as e:
            self.log.info('File % does not exists' % path)

        if file_info:
            model = ModelUtils.update_file_model(ModelUtils.create_empty_file_model(path), file_info)

        model['writable'] = self._is_editor(file_info)
        if content:
            content = self._read_file(file_info, format)
            if format is None:
                format = "text"

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

    # can't be async because SQLite (used for jupyter notebooks) doesn't allow multithreaded operations by default
    def _notebook_model(self, path, content):
        file_info = self.file_api.stat_info(path, self.cs3_config.endpoint)

        model = ModelUtils.update_file_model(ModelUtils.create_empty_file_model(path), file_info)
        model['type'] = 'notebook'

        if content:
            file_content = self._read_file(file_info)
            nb = nbformat.reads(file_content, as_version=4)
            self.mark_trusted_cells(nb, path)
            model['content'] = nb
            model['format'] = 'json'
            self.validate_notebook_model(model)

        return model

    @asyncify
    def _is_dir(self, path):
        if path == '/' or path == '' or path is None:
            return True

        path = FileUtils.normalize_path(path)
        stat = self.storage_api.stat(path)
        return stat.status.code == cs3code.CODE_OK and stat.info.type == resource_types.RESOURCE_TYPE_CONTAINER

    @asyncify
    def _save_file(self, path, content, format):
        if format not in {'text', 'base64'}:
            raise web.HTTPError(400, "Must specify format of file contents as 'text' or 'base64'", )

        try:
            if format is None or format == 'text':
                bcontent = content.encode('utf8')
            else:
                b64_bytes = content.encode('ascii')
                bcontent = decodebytes(b64_bytes)

            self.file_api.write_file(path, bcontent, self.cs3_config.endpoint, format)

        except Exception as e:
            self.log.error(u'Error saving: %s %s', path, e)
            raise web.HTTPError(400, u'Error saving %s: %s' % (path, e))

    # can't be async because SQLite (used for jupyter notebooks) doesn't allow multithreaded operations by default
    def _save_notebook(self, path, nb, format):

        nb_content = nbformat.writes(nb)
        try:
            self.file_api.write_file(path, nb_content, self.cs3_config.endpoint, format)

        except Exception as e:
            self.log.error(u'Error saving: %s %s', path, e)
            raise web.HTTPError(400, u'Error saving %s: %s' % (path, e))

    @asyncify
    def _save_directory(self, path):

        if self.is_hidden(path) and not self.allow_hidden:
            raise web.HTTPError(400, u'Cannot create hidden directory %s' % path)

        if self._is_dir(path):
            raise web.HTTPError(400, u'Directory %r already exists %s' % path)

        if self.file_exists(path):
            raise web.HTTPError(400, u'Not a directory %s' % path)

        self.file_api.create_directory(path, self.cs3_config.endpoint)

    def _is_editor(self, file_info):
        '''
        This determines if the user can write to the file or not
        (check permissions of the file, share and check if the file is locked)
        '''
        is_editor = True

        if not file_info:
            return is_editor

        # check file permissions
        if ShareUtils.map_permissions_to_role(file_info['permissions']) == Role.VIEWER:
            is_editor = False

        # check if file is shared with me
        role = self.share_api.get_share_received_role(file_info['filepath'])
        if is_editor and role and role == Role.VIEWER:
            is_editor = False

        # check if file is locked
        if self.lock_api.is_file_locked(file_info):
            is_editor = False

        return is_editor


    #
    # Notebook hack - disable checkpoint
    #
    @asyncify
    def delete(self, path):
        path = path.strip('/')
        if not path:
            raise web.HTTPError(400, "Can't delete root")
        self.delete_file(path)

    @asyncify
    def rename(self, old_path, new_path):
        self.rename_file(old_path, new_path)

    def create_checkpoint(self, path):
        return {'id': 'checkpoint', 'last_modified': "0"}

    def restore_checkpoint(self, checkpoint_id, path):
        pass

    def list_checkpoints(self, path):
        return [{'id': 'checkpoint', 'last_modified': "0"}]

    def delete_checkpoint(self, checkpoint_id, path):
        pass
