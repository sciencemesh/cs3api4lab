from notebook.services.contents.manager import ContentsManager

class CS3APIsManager(ContentsManager):

    def dir_exists(self, path):
        """Does a directory exist at the given path?
        Like os.path.isdir
        Override this method in subclasses.
        Parameters
        ----------
        path : string
            The path to check
        Returns
        -------
        exists : bool
            Whether the path does indeed exist.
        """
        raise NotImplementedError('cs3: missing')

    def is_hidden(self, path):
        """Is path a hidden directory or file?
        Parameters
        ----------
        path : string
            The path to check. This is an API path (`/` separated,
            relative to root dir).
        Returns
        -------
        hidden : bool
            Whether the path is hidden.
        """
        raise NotImplementedError('cs3: missing')

    def file_exists(self, path=''):
        """Does a file exist at the given path?
        Like os.path.isfile
        Override this method in subclasses.
        Parameters
        ----------
        path : string
            The API path of a file to check for.
        Returns
        -------
        exists : bool
            Whether the file exists.
        """
        raise NotImplementedError('cs3: missing')

    def get(self, path, content=True, type=None, format=None):
        """Get a file or directory model."""
        raise NotImplementedError('cs3: missing')

    def save(self, model, path):
        """
        Save a file or directory model to path.
        Should return the saved model with no content.  Save implementations
        should call self.run_pre_save_hook(model=model, path=path) prior to
        writing any data.
        """
        raise NotImplementedError('cs3: missing')

    def delete_file(self, path):
        """Delete the file or directory at path."""
        raise NotImplementedError('cs3: missing')

    def rename_file(self, old_path, new_path):
        """Rename a file or directory."""
        raise NotImplementedError('cs3: missing')

    

