from cs3api4lab.auth.authenticator import Authenticator


class RevaPassword(Authenticator):

    def __init__(self, config=None, log=None):
        super().__init__(config, log)

    def refresh_token(self, client_id=None, client_secret_or_token=None):
        self.token = self._auth_in_iop(self.config.client_secret, "basic")
