import mimetypes

from datetime import datetime
from IPython.utils import tz
from cs3api4lab.utils.share_utils import ShareUtils

class ModelUtils:
    date_fmt = '%Y-%m-%dT%H:%M:%SZ'
    TYPE_FILE = 1
    TYPE_DIRECTORY = 2

    @staticmethod
    def create_respond_model():

        model = {}
        model['name'] = "/"
        model['path'] = "/"
        model['last_modified'] = datetime.now(tz=tz.UTC).strftime(ModelUtils.date_fmt)
        model['created'] = datetime.now(tz=tz.UTC).strftime(ModelUtils.date_fmt)
        model['mimetype'] = None
        model['writable'] = False
        model['type'] = None
        model['size'] = None
        model['type'] = 'directory'
        model['content'] = []
        model['format'] = 'json'
        model['owner'] = None
        model['opaque_id'] = None
        return model

    @staticmethod
    def parse_date(timestamp):
        try:
            date = datetime.fromtimestamp(timestamp, tz=tz.UTC).strftime(ModelUtils.date_fmt)
        except ValueError as e:
            date = datetime.fromtimestamp(0, tz=tz.UTC).strftime(ModelUtils.date_fmt)
        return date

    @staticmethod
    def map_share_to_base_model(share, stat, optional={}):
        writable = False
        if hasattr(share.permissions.permissions,
                   'initiate_file_upload') and share.permissions.permissions.initiate_file_upload is True:
            writable = True
        model = {}
        model['name'] = stat['filepath'].rsplit('/', 1)[-1]
        model['path'] = stat['filepath']
        model['last_modified'] = ModelUtils.parse_date(share.mtime.seconds)
        model['created'] = ModelUtils.parse_date(share.ctime.seconds)
        model['content'] = None
        model['format'] = None
        model['writable'] = writable
        model['opaque_id'] = share.id.opaque_id

        if 'owner' in optional:
            model['owner'] = optional['owner']

        return model

    @staticmethod
    def map_share_to_file_model(share, stat, optional={}):

        model = ModelUtils.map_share_to_base_model(share, stat, optional)
        model['size'] = stat['size']
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(stat['filepath'])[0]

        return model

    @staticmethod
    def map_share_to_dir_model(share, stat, optional={}):

        model = ModelUtils.map_share_to_base_model(share, stat, optional)
        model['size'] = None
        model['type'] = 'directory'
        model['mimetype'] = None
        return model

    # @TODO this code was copied from cs3apismanager - needs clean up
    @staticmethod
    def convert_container_to_base_model(path, cs3_container):
        size = None
        writable = False
        created = datetime(1970, 1, 1, 0, 0, tzinfo=tz.UTC).strftime(ModelUtils.date_fmt)
        last_modified = datetime(1970, 1, 1, 0, 0, tzinfo=tz.UTC).strftime(ModelUtils.date_fmt)

        #
        # Get data from container element
        #
        for cs3_model in cs3_container:
            if cs3_model.path == path:
                size = cs3_model.size
                created = datetime.fromtimestamp(cs3_model.mtime.seconds, tz=tz.UTC).strftime(ModelUtils.date_fmt)
                last_modified = datetime.fromtimestamp(cs3_model.mtime.seconds, tz=tz.UTC).strftime(ModelUtils.date_fmt)

                if ShareUtils.map_permissions_to_role(cs3_model.permission_set) == "editor":
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

    @staticmethod
    def convert_container_to_file_model(cs3_model, cs3_container):

        model = ModelUtils.convert_container_to_base_model(cs3_model.path, cs3_container)
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(cs3_model.path)[0]

        return model

    @staticmethod
    def convert_container_to_notebook_model(cs3_model, cs3_container):

        model = ModelUtils.convert_container_to_base_model(cs3_model.path, cs3_container)
        model['type'] = 'notebook'
        model['mimetype'] = mimetypes.guess_type(cs3_model.path)[0]

        return model

    @staticmethod
    def convert_container_to_directory_model(path, cs3_container, content=True):

        model = ModelUtils.convert_container_to_base_model(path, cs3_container)
        model['size'] = None
        model['type'] = 'directory'

        if content:
            model['content'] = contents = []
            model['format'] = 'json'

            for cs3_model in cs3_container:
                if cs3_model.type == ModelUtils.TYPE_DIRECTORY:
                    sub_model = ModelUtils.convert_container_to_base_model(cs3_model.path, cs3_container)
                    sub_model['size'] = None
                    sub_model['type'] = 'directory'
                    contents.append(sub_model)
                elif cs3_model.type == ModelUtils.TYPE_FILE:
                    if type == 'notebook' or (type is None and path.endswith('.ipynb')):
                        contents.append(
                            ModelUtils.convert_container_to_notebook_model(cs3_model, cs3_container)
                        )
                    else:
                        contents.append(
                            ModelUtils.convert_container_to_file_model(cs3_model, cs3_container)
                        )

        return model
