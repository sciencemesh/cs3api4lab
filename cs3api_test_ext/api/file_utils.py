import cs3.storage.provider.v1beta1.resources_pb2 as cs3spr


class FileUtils:
    @staticmethod
    def get_reference(fileid, home_dir, endpoint=None):
        if len(fileid) > 0 and fileid[0] == '/':
            # assume this is a filepath
            if len(home_dir) > 0 and not fileid.startswith(home_dir):
                fileid = home_dir + fileid
            file = cs3spr.Reference(path=fileid)
            return file

        if endpoint == 'default' or endpoint is None:
            raise IOError('A CS3API-compatible storage endpoint must be identified by a storage UUID')
        # assume we have an opaque fileid
        return cs3spr.Reference(id=cs3spr.ResourceId(storage_id=endpoint, opaque_id=fileid))