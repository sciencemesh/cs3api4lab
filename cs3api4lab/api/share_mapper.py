from cs3api4lab.config.config_manager import Cs3ConfigManager


# ToDO: Add support for multiple access -> store layout in the diffident path
# ToDO: Clear cache records for multiple paths
class Mapper:
    map_cache = {}
    config = {}

    def __init__(self) -> None:
        super().__init__()
        self.config = Cs3ConfigManager().get_config()

    def remap_dir_model(self, dir_model):

        if dir_model['content'] is None or len(dir_model['content']) == 0 or self.config['map_share_path'] is False:
            return dir_model

        self.map_cache = {}

        root_dirs = self.config['root_dir_list']
        for idx, model in enumerate(dir_model['content']):
            src = model['path']
            if src.startswith(root_dirs):
                dst = src
                for root in root_dirs:
                    if src.startswith(root):
                        dst = "/".join(src.split('/')[3:-1]) + "/" + model['name']
                        break
                self.map_cache[dst] = src
                dir_model['content'][idx]['path'] = dst

        return dir_model

    def remap_path(self, path):
        if self.config['map_share_path'] is False:
            return path
        dst = self.map_cache.get(path)
        return dst if dst is not None else path


class ShareMapper:
    __mapper_instance = None

    @classmethod
    def get_mapper(cls):
        if not cls.__mapper_instance:
            cls.__mapper_instance = Mapper()
        return cls.__mapper_instance
