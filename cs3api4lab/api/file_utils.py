import cs3.storage.provider.v1beta1.resources_pb2 as storage_provider


class FileUtils:
    @staticmethod
    def get_reference(file_id, home_dir, endpoint=None):
        if len(file_id) > 0 and file_id[0] == '/':
            # assume this is a filepath
            # if len(home_dir) > 0 and not file_id.startswith(home_dir):
            #     file_id = home_dir + file_id
            file = storage_provider.Reference(path=file_id)
            return file

        if endpoint == 'default' or endpoint is None:
            raise IOError('A CS3API-compatible storage endpoint must be identified by a storage UUID')
        # assume we have an opaque fileid
        return storage_provider.Reference(id=storage_provider.ResourceId(storage_id=endpoint, opaque_id=file_id))