from notebook.services.contents.checkpoints import Checkpoints


class CS3APIsCheckpoints(Checkpoints):

    def create_checkpoint(self, contents_mgr, path):
        """Create a checkpoint."""
        # raise NotImplementedError('cs3: missing')
        pass

    def restore_checkpoint(self, contents_mgr, checkpoint_id, path):
        """Restore a checkpoint"""
        # raise NotImplementedError('cs3: missing')
        pass

    def rename_checkpoint(self, checkpoint_id, old_path, new_path):
        """Rename a single checkpoint from old_path to new_path."""
        # raise NotImplementedError('cs3: missing')
        pass

    def delete_checkpoint(self, checkpoint_id, path):
        """delete a checkpoint for a file"""
        # raise NotImplementedError('cs3: missing')
        pass

    def list_checkpoints(self, path):
        """Return a list of checkpoints for a given file"""
        # raise NotImplementedError('cs3: missing')
        return []
