from notebook.services.contents.checkpoints import Checkpoints


class CS3APIsCheckpoints(Checkpoints):

    def create_checkpoint(self, contents_mgr, path):
        """Create a checkpoint."""
        # raise NotImplementedError('cs3: missing')
        print("->>>>>> CS3APIsCheckpoints create_checkpoint contents_mgr: ", contents_mgr)
        pass

    def restore_checkpoint(self, contents_mgr, checkpoint_id, path):
        """Restore a checkpoint"""
        # raise NotImplementedError('cs3: missing')
        print("->>>>>> CS3APIsCheckpoints restore_checkpoint checkpoint_id: ", checkpoint_id)
        pass

    def rename_checkpoint(self, checkpoint_id, old_path, new_path):
        """Rename a single checkpoint from old_path to new_path."""
        # raise NotImplementedError('cs3: missing')
        print("->>>>>> CS3APIsCheckpoints rename_checkpoint new_path: ", new_path)
        pass

    def delete_checkpoint(self, checkpoint_id, path):
        """delete a checkpoint for a file"""
        # raise NotImplementedError('cs3: missing')
        print("->>>>>> CS3APIsCheckpoints delete_checkpoint ", "checkpoint_id:", checkpoint_id, "path:", path)
        pass

    def list_checkpoints(self, path):
        """Return a list of checkpoints for a given file"""
        # raise NotImplementedError('cs3: missing')
        print("->>>>>> CS3APIsCheckpoints list_checkpoints path: ", path)
        return []
