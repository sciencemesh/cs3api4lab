from base64 import decodebytes
from datetime import datetime
import nbformat
import mimetypes
from notebook.services.contents.manager import ContentsManager
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from tornado import web
from notebook import _tz as tz
from nbformat.v4 import new_notebook
from cs3api4lab.config.config_manager import Cs3ConfigManager


class CS3APIsManager(ContentsManager):
    cs3_config = None
    log = None

    # ToDo: Change to cs3 Type
    TYPE_FILE = 1
    TYPE_DIRECTORY = 2

    file_api = None

    def __init__(self, parent, log):
        self.cs3_config = Cs3ConfigManager.get_config()
        self.log = log
        self.file_api = Cs3FileApi(self.log)

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

        return self._is_dir(path)

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
        path = self._normalize_path(path)
        parts = path.split('/')
        if any(part.startswith('.') for part in parts):
            return True
        return False

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
        parent_path = self._get_parent_path(path)
        path = self._normalize_path(path)
        try:
            cs3_container = self.file_api.read_directory(parent_path, self.cs3_config['endpoint'])
        except Exception as ex:
            self.log.error(u'Error while reading container: %s %s', path, ex, exc_info=True)
            raise web.HTTPError(500, u'Unexpected error while reading container: %s %s' % (path, ex))

        for cs3_model in cs3_container:
            if cs3_model.type == self.TYPE_FILE and cs3_model.path == path:
                return True

        return False

    def get(self, path, content=True, type=None, format=None):
        """Get a file, notebook or directory model."""
        path = self._normalize_path(path)
        if type in (None, 'directory') and self._is_dir(path):
            model = self._dir_model(path, content=content)
        elif type == 'notebook' or (type is None and path.endswith('.ipynb')):
            model = self._notebook_model(path, content=content)
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
        path = self._normalize_path(path)
        self._check_write_permissions(path)

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
                self._save_notebook(path, nb)

                # ToDo: Implements save to checkpoint
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

    def delete_file(self, path):
        """Delete the file or directory at path."""
        path = self._normalize_path(path)
        try:
            self.file_api.remove(path, self.cs3_config['endpoint'])

        except FileNotFoundError as e:
            self.log.error(u'File not found error: %s %s', path, e, exc_info=True)
            raise web.HTTPError(404, u'No such file or directory: %s %s' % (path, e))

        except Exception as e:
            self.log.error(u'Unknown error delete file: %s %s', path, e, exc_info=True)
            raise web.HTTPError(500, u'Unknown error delete file: %s %s' % (path, e))

    def rename_file(self, old_path, new_path):
        """Rename a file or directory."""

        if new_path == old_path:
            return

        #
        # ToDo: Implements validate file like: notebook/services/contents/filemanager.py:587 using Reva API
        #
        old_path = self._normalize_path(old_path)
        new_path = self._normalize_path(new_path)

        # Move the file
        try:
            self.file_api.move(old_path, new_path, self.cs3_config['endpoint'])
        except Exception as e:
            self.log.error(u'Error renaming file: %s %s', old_path, e)
            raise web.HTTPError(500, u'Error renaming file: %s %s' % (old_path, e))

    def new(self, model=None, path=''):

        path = path.strip('/')
        self._check_write_permissions(path)

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

        # ToDo: Fix writable flag - based on container status
        model['writable'] = True

        return model

    def _normalize_path(self, path):

        if len(path) > 0 and path[0] != '/':
            path = '/' + path
        elif path == '' or path is None:
            path = '/'
        return path

    def _get_parent_path(self, path):

        directories = path.rsplit('/')
        directories.reverse()

        if directories[0] != '':
            path = self._replace_last(str(path), directories[0])

        return self._normalize_path(path)

    def _replace_last(self, source_string, replace_what, replace_with=""):
        head, _sep, tail = source_string.rpartition(replace_what)
        return head + replace_with + tail

    def _read_file(self, path):

        content = ''
        for chunk in self.file_api.read_file(path, self.cs3_config['endpoint']):
            content += chunk.decode('utf-8')

        return content

    def _dir_model(self, path, content):

        cs3_container = self.file_api.read_directory(path, self.cs3_config['endpoint'])
        model = self._convert_container_to_directory_model(path, cs3_container, content)

        return model

    def _file_model(self, path, content, format):

        model, tmp_model = self._create_base_model_from_cs3_container(path)
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(tmp_model.path)[0]

        if content:
            content = self._read_file(tmp_model.path)

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

    def _notebook_model(self, path, content):

        model, tmp_model = self._create_base_model_from_cs3_container(path)
        model['type'] = 'notebook'

        if content:
            file_content = self._read_file(tmp_model.path)
            nb = nbformat.reads(file_content, as_version=4)
            self.mark_trusted_cells(nb, path)
            model['content'] = nb
            model['format'] = 'json'
            self.validate_notebook_model(model)

        return model

    def _is_dir(self, path):

        if path == '/' or path == '' or path is None:
            return True

        parent_path = self._get_parent_path(path)
        path = self._normalize_path(path)

        try:
            cs3_container = self.file_api.read_directory(parent_path, self.cs3_config['endpoint'])
        except Exception as ex:
            self.log.error(u'Error while reading container: %s %s', path, ex, exc_info=True)
            raise web.HTTPError(500, u'Unexpected error while reading container: %s %s' % (path, ex))

        for cs3_model in cs3_container:

            if cs3_model.type == self.TYPE_DIRECTORY and cs3_model.path == path:
                return True
            if cs3_model.type == self.TYPE_FILE and cs3_model.path == path:
                return False

        return False

    def _create_base_model_from_cs3_container(self, path):

        parent_path = self._get_parent_path(path)

        cs3_container = self.file_api.read_directory(parent_path, self.cs3_config['endpoint'])

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

                if str(cs3_model.permission_set.create_container).lower() == "true":
                    writable = True

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

    def _save_file(self, path, content, format):

        if format not in {'text', 'base64'}:
            raise web.HTTPError(400, "Must specify format of file contents as 'text' or 'base64'", )

        try:
            if format == 'text':
                bcontent = content.encode('utf8')
            else:
                b64_bytes = content.encode('ascii')
                bcontent = decodebytes(b64_bytes)

            self.file_api.write_file(path, bcontent, self.cs3_config['endpoint'])

        except Exception as e:
            self.log.error(u'Error saving: %s %s', path, e)
            raise web.HTTPError(400, u'Error saving %s: %s' % (path, e))

    def _save_notebook(self, path, nb):

        nb_content = nbformat.writes(nb)
        try:
            self.file_api.write_file(path, nb_content, self.cs3_config['endpoint'])

        except Exception as e:
            self.log.error(u'Error saving: %s %s', path, e)
            raise web.HTTPError(400, u'Error saving %s: %s' % (path, e))

    def _save_directory(self, path):

        if self.is_hidden(path) and not self.allow_hidden:
            raise web.HTTPError(400, u'Cannot create hidden directory %s' % path)

        if self._is_dir(path):
            raise web.HTTPError(400, u'Directory %r already exists %s' % path)

        if self.file_exists(path):
            raise web.HTTPError(400, u'Not a directory %s' % path)

        self.file_api.create_directory(path, self.cs3_config['endpoint'])

    def _check_write_permissions(self, path):

        parent = self._get_parent_path(path)
        stat = self.file_api.stat(parent)

        if hasattr(stat['permissions'], 'initiate_file_upload') and stat['permissions'].initiate_file_upload is False:
            raise web.HTTPError(400, u'The path %s is not writable' % parent)

#
    # Notebook hack - disable checkpoint
    #
    def delete(self, path):
        path = path.strip('/')
        if not path:
            raise web.HTTPError(400, "Can't delete root")
        self.delete_file(path)

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
