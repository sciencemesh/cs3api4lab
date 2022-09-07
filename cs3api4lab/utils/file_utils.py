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
    def calculate_content_size(content):
        if isinstance(content, str):
            content_len = len(content)
        else:
            content_len = len(content.decode('utf-8'))
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
    def get_my_shares_path_prefix(config):
        if config.mount_dir == "/":
            return config.home_dir + "/" + config.shared_folder
        else:
            return "/" + config.shared_folder

    @staticmethod
    def get_share_path_prefix(config):
        if config.mount_dir == "/" and config.home_dir != "/":
            return config.home_dir
        else:
            return '/reva/' + config.client_id

    @staticmethod
    def remove_drives_names(path):
        for drive in ["cs3drive:", "cs3driveShareWithMe:", "cs3driveShareByMe:", "/cs3drive:", "/cs3driveShareWithMe:", "/cs3driveShareByMe:"]:
            if path.startswith(drive):
                path = path.replace(drive, "/")
                break
        return FileUtils.normalize_path(path)

    @staticmethod
    def handle_drive(path, config):
        drive = FileUtils.get_drive(path)
        if drive:
            path = FileUtils.replace_drive_with_directory(path, drive, config)
        return path, drive

    @staticmethod
    def get_drive(path):
        has_root = path.startswith("/")
        has_colon = ":" in path
        for drive in ["cs3driveShareWithMe", "cs3driveShareByMe", "cs3drive"]:
            if has_root:
                drive = "/" + drive
            if has_colon:
                drive = drive + ":"
            if path.startswith(drive):
                return drive
        return None

    @staticmethod
    def replace_drive_with_directory(path, drive, config):
        if "cs3driveShareWithMe" in drive:
            prefix = FileUtils.get_my_shares_path_prefix(config)
            path = path.replace(drive, prefix + "/")
        if "cs3driveShareByMe" in drive:
            prefix = FileUtils.get_share_path_prefix(config)
            path = path.replace(drive, "/")
            path = prefix + path
        else:
            path = path.replace(drive, "")

        return path
