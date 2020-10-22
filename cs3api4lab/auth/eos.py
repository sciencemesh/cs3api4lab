import os
from io import TextIOWrapper

from jupyter_core.paths import jupyter_config_path
from notebook.services.config import ConfigManager

from cs3api4lab.auth.authenticator import Authenticator


class Eos(Authenticator):
    tokens = {}

    def __init__(self, config=None, log=None):

        self.config = config
        file = None
        if "eos_file" in self.config and self.config['eos_file'] is not "":

            try:
                file = open(self.config['eos_file'], "r")
                eos_token = file.read()
            except IOError as e:
                raise IOError(f"Error opening token file {self.config['eos_file']} exception: {e}")
            finally:
                if file is not None:
                    file.close()

        elif "eos_token" in self.config and self.config['eos_token'] is not "":
            eos_token = self.config['eos_token']
        else:
            raise AttributeError("Config haven't EOS token or token file.")

        self.tokens = eos_token.split(':')
        if len(self.tokens) != 3 or self.tokens[0] != 'oauth2':
            raise AttributeError("It's not valid EOS token.")

    def authenticate(self, client_id):
        return self.tokens[1]
