import mimetypes

from datetime import datetime
from IPython.utils import tz


class ModelUtils:
    date_fmt = '%Y-%m-%dT%H:%M:%SZ'

    @staticmethod
<<<<<<< HEAD
<<<<<<< HEAD
    def create_respond_model():
=======
    def _create_respond_model():
>>>>>>> c3f5ea6 (Locking for shares part 1 #11)
=======
    def create_respond_model():
>>>>>>> 8e0a78a (correct method names in model_utils)

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

        return model

    @staticmethod
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 8e0a78a (correct method names in model_utils)
    def map_share_to_file_model(share, stat):

        model = ModelUtils._map_share_to_base_model(share, stat)
        model['size'] = stat['size']
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(stat['filepath'])[0]

        return model

    @staticmethod
    def map_share_to_dir_model(share, stat):

        model = ModelUtils._map_share_to_base_model(share, stat)
        model['size'] = None
        model['type'] = 'directory'
        model['mimetype'] = None
        return model

    @staticmethod
<<<<<<< HEAD
=======
>>>>>>> c3f5ea6 (Locking for shares part 1 #11)
=======
>>>>>>> 8e0a78a (correct method names in model_utils)
    def _map_share_to_base_model(share, stat):

        created = datetime.fromtimestamp(share.ctime.seconds, tz=tz.UTC).strftime(ModelUtils.date_fmt)
        last_modified = datetime.fromtimestamp(share.mtime.seconds, tz=tz.UTC).strftime(ModelUtils.date_fmt)

        writable = False
        if hasattr(share.permissions.permissions,
                   'initiate_file_upload') and share.permissions.permissions.initiate_file_upload is True:
            writable = True

        model = {}
        model['name'] = stat['filepath'].rsplit('/', 1)[-1]
        model['path'] = stat['filepath']
        model['last_modified'] = last_modified
        model['created'] = created
        model['content'] = None
        model['format'] = None
        model['writable'] = writable
<<<<<<< HEAD
<<<<<<< HEAD
=======
        return model

    @staticmethod
    def _map_share_to_file_model(share, stat):

        model = ModelUtils._map_share_to_base_model(share, stat)
        model['size'] = stat['size']
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(stat['filepath'])[0]

        return model

    @staticmethod
    def _map_share_to_dir_model(share, stat):

        model = ModelUtils._map_share_to_base_model(share, stat)
        model['size'] = None
        model['type'] = 'directory'
        model['mimetype'] = None
>>>>>>> c3f5ea6 (Locking for shares part 1 #11)
=======
>>>>>>> 8e0a78a (correct method names in model_utils)
        return model