import mimetypes

from datetime import datetime
from IPython.utils import tz


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

        return model

    @staticmethod
    def parse_date(timestamp):
        try:
            date = datetime.fromtimestamp(timestamp, tz=tz.UTC).strftime(ModelUtils.date_fmt)
        except ValueError as e:
            date = datetime.fromtimestamp(0, tz=tz.UTC).strftime(ModelUtils.date_fmt)
        return date

    @staticmethod
    def map_share_to_base_model(share, stat):
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
        return model

    @staticmethod
    def map_share_to_file_model(share, stat):

        model = ModelUtils.map_share_to_base_model(share, stat)
        model['size'] = stat['size']
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(stat['filepath'])[0]

        return model

    @staticmethod
    def map_share_to_dir_model(share, stat):

        model = ModelUtils.map_share_to_base_model(share, stat)
        model['size'] = None
        model['type'] = 'directory'
        model['mimetype'] = None
        return model
