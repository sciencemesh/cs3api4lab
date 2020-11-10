from cs3api4lab.auth.oauth import Oauth


class Eos(Oauth):

    def __init__(self, config=None, log=None):
        super().__init__(config, log)

    def _refresh_token_from_file_or_config(self):

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

        eos_split_token = eos_token.split(':')
        if len(eos_split_token) != 3 or eos_split_token[0] != 'oauth2' \
                or self._check_token(eos_split_token[1]) is False:
            raise self.raise_401_error()

        return eos_split_token[1]
