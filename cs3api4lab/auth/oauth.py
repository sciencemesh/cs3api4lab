from cs3api4lab.auth.authenticator import Authenticator


class Oauth(Authenticator):

    def __init__(self, config=None, log=None):
        super().__init__(config, log)

    def refresh_token(self):
        oauth_token = self._refresh_token_from_file_or_config()
        self.token = self._auth_in_iop(oauth_token, "bearer")

    def _refresh_token_from_file_or_config(self):
        """
        Get OAuth token from file or config value and try to convert IOP token (authentication process)
        """

        if "oauth_file" in self.config and self.config['oauth_file'] != "":

            try:
                with open(self.config['oauth_file'], "r") as file:
                    oauth_token = file.read()
            except IOError as e:
                raise IOError(f"Error opening token file {self.config['oauth_file']} exception: {e}")

        elif "oauth_token" in self.config and self.config['oauth_token'] != "":
            oauth_token = self.config['oauth_token']
        else:
            raise AttributeError("Config hasn't OAuth token or token file.")

        if self._check_token(oauth_token) is False:
            self.raise_401_error()

        return oauth_token
