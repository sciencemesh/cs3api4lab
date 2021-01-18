import cs3.storage.provider.v1beta1.resources_pb2 as storage_provider

from cs3api4lab.config.config_manager import Cs3ConfigManager


class FileUtils:

    @staticmethod
    def get_reference(file_id, endpoint=None):

        if len(file_id) > 0 and file_id[0] == '/':
            # assume this is a filepath
            file_id = FileUtils._check_and_transform_file_path(file_id)
            file = storage_provider.Reference(path=file_id)
            return file

        if endpoint == 'default' or endpoint is None:
            raise IOError('A CS3API-compatible storage endpoint must be identified by a storage UUID')
        # assume we have an opaque fileid
        return storage_provider.Reference(id=storage_provider.ResourceId(storage_id=endpoint, opaque_id=file_id))

    @staticmethod
    def _check_and_transform_file_path(file_id):

        config = Cs3ConfigManager.get_config()
        has_root_dir = file_id.startswith(config["root_dir_list"])

        if len(config["home_dir"]) > 0 and not file_id.startswith(config["home_dir"]) and not has_root_dir:
            file_id = config["home_dir"] + file_id

        return file_id