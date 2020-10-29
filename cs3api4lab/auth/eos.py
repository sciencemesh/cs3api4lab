from cs3api4lab.auth.authenticator import Authenticator


class Eos(Authenticator):
    tokens = {}

    def __init__(self, config=None, log=None):
        self.config = config

    def authenticate(self, client_id):

        if client_id not in self.tokens:
            self._refresh_token_from_file_or_config(client_id)

        if client_id in self.tokens and self.check_token(self.tokens[client_id][1]) is False:
            self._refresh_token_from_file_or_config(client_id)

        return self.tokens[client_id][1]

    def _refresh_token_from_file_or_config(self, client_id):

        if "eos_file" in self.config and self.config['eos_file'] is not "":

            try:
                with open(self.config['eos_file'], "r") as file:
                    eos_token = file.read()
            except IOError as e:
                raise IOError(f"Error opening token file {self.config['eos_file']} exception: {e}")

        elif "eos_token" in self.config and self.config['eos_token'] is not "":
            eos_token = self.config['eos_token']
        else:
            raise AttributeError("Config hasn't EOS token or token file.")
        self.tokens[client_id] = eos_token.split(':')
        if len(self.tokens[client_id]) != 3 or self.tokens[client_id][0] != 'oauth2':
            raise AttributeError("It's not valid EOS token.")
