import mimetypes
import cs3.storage.provider.v1beta1.resources_pb2 as resource_types

from tornado import web
from datetime import datetime
from IPython.utils import tz
from cs3api4lab.utils.share_utils import ShareUtils

class ModelUtils:
    date_fmt = '%Y-%m-%dT%H:%M:%SZ'

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
        except ValueError:
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

    @staticmethod
    def convert_container_to_base_model(path, cs3_container):
        created, last_modified, size, writable = ModelUtils.get_info_from_container(cs3_container, path)

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
                if cs3_model.type == resource_types.RESOURCE_TYPE_CONTAINER:
                    sub_model = ModelUtils.convert_container_to_base_model(cs3_model.path, cs3_container)
                    sub_model['size'] = None
                    sub_model['type'] = 'directory'
                    contents.append(sub_model)
                elif cs3_model.type == resource_types.RESOURCE_TYPE_FILE:
                    if type == 'notebook' or (type is None and path.endswith('.ipynb')):
                        contents.append(
                            ModelUtils.convert_container_to_notebook_model(cs3_model, cs3_container)
                        )
                    else:
                        contents.append(
                            ModelUtils.convert_container_to_file_model(cs3_model, cs3_container)
                        )
                else: #(TODO check why this wasnt here)
                    raise web.HTTPError(500, u'Unexpected type: %s %s' % (cs3_model.path, cs3_model.type))

        return model

    @staticmethod
    def create_base_model_from_cs3_container(path, cs3_container):
        cs3_model = None
        for cs3_tmp_model in cs3_container:
            if cs3_tmp_model.type == resource_types.RESOURCE_TYPE_FILE and cs3_tmp_model.path == path:
                cs3_model = cs3_tmp_model

        if cs3_model is None:
            raise web.HTTPError(404, u'%s does not exist' % path)

        model = ModelUtils.convert_container_to_base_model(cs3_model.path, cs3_container)
        return model, cs3_model

    @staticmethod
    def get_info_from_container(cs3_container, path):
        size = None
        writable = False
        created = ModelUtils.parse_date(0)
        last_modified = ModelUtils.parse_date(0)

        for cs3_model in cs3_container:
            if cs3_model.path == path:
                size = cs3_model.size
                created = ModelUtils.parse_date(cs3_model.mtime.seconds)
                last_modified = ModelUtils.parse_date(cs3_model.mtime.seconds)

                if ShareUtils.map_permissions_to_role(cs3_model.permission_set) == "editor":
                    writable = True

        return created, last_modified, size, writable
