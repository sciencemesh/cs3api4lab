import urllib.parse

import cs3.storage.provider.v1beta1.resources_pb2 as storage_provider
from cs3api4lab.config.config_manager import Cs3ConfigManager


class FileUtils:

    @staticmethod
    def get_reference(file_id, endpoint=None):

        if len(file_id) > 0 and file_id[0] == '/':
            # assume this is a filepath
            file_id = FileUtils.check_and_transform_file_path(file_id)
            file = storage_provider.Reference(path=file_id)
            return file

        if endpoint == 'default' or endpoint is None:
            raise IOError('A CS3API-compatible storage endpoint must be identified by a storage UUID')
        # assume we have an opaque fileid
        return storage_provider.Reference(resource_id=storage_provider.ResourceId(storage_id=endpoint, opaque_id=file_id))

    @staticmethod
    def check_and_transform_file_path(file_id):
        config = Cs3ConfigManager().get_config() #note: can cause problems in tests because of the config, it should be passed as an argument

        has_root_dir = file_id.startswith(config.root_dir_list)

        if len(config.mount_dir) > 0 and not file_id.startswith(config.mount_dir) and not has_root_dir:
            file_id = config.mount_dir + file_id

        return file_id

    @staticmethod
    def calculate_content_size(content, format=None):
        if format == "text":
            content_len = len(content.decode('utf-8'))
        else:
            content_len = len(content)

        content_size = str(content_len)
        return content_size

    @staticmethod
    def normalize_path(path):
        if len(path) > 0 and path[0] != '/':
            path = '/' + path
        elif path == '' or path is None:
            path = '/'
        return path

    @staticmethod
    def fix_dev_opaque(opaque_id, dev_env):  # remove after https://github.com/cs3org/reva/issues/3243 is fixed
        if dev_env:
            opaque_id = opaque_id.replace('fileid-/', 'fileid-').replace('+', ' ')
            opaque_id = urllib.parse.quote_plus(opaque_id, '')

        return opaque_id
