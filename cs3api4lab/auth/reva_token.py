from tornado import web

from cs3api4lab.auth.authenticator import Authenticator


class RevaTokenAuth(Authenticator):

    def __init__(self, config=None, log=None):
        self.config = config

    def authenticate(self, client_id):
        if self.check_token(self.config['client_token']) is False:
            self.config['client_token'] = self.refresh_token()

        return self.config['client_token']

    def refresh_token(self, refresh_token=None):
        raise web.HTTPError(401, u'Failed to authenticate user', reason="unauthenticated")
