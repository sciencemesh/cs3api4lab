import os
from pathlib import Path
from unittest import TestCase

from tornado import web
from traitlets.config import LoggingConfigurable

from cs3api4lab.auth.authenticator import Authenticator, Auth
from cs3api4lab.auth.reva_password import RevaPassword
from cs3api4lab.config.config_manager import Cs3ConfigManager


class TestAuthenticator(TestCase, LoggingConfigurable):

    def setUp(self) -> None:
        Auth.clean()

    def test_create(self):
        authenticator = Auth.get_authenticator(log=self.log)
        self.assertIsInstance(authenticator, RevaPassword)

    def test_create_wrong_class(self):
        config_manager = Cs3ConfigManager()
        config = config_manager.get_config()
        config['authenticator_class'] = 'cs3api4lab.auth.reva_password.TestPassword'

        with self.assertRaises(AttributeError):
            authenticator = Auth.get_authenticator(log=self.log)
            self.assertNotIsInstance(authenticator.instance, RevaPassword)

    def test_authenticate_riva_password(self):
        authenticator = Auth.get_authenticator(log=self.log)
        token = authenticator.authenticate('einstein')
        tokens = token.split('.')
        self.assertEqual(len(tokens), 3)

    def test_authenticate_riva_token(self):
        authenticator = Auth.get_authenticator(log=self.log)
        token_from_cs3 = authenticator.authenticate('einstein')

        token_config = {
            'authenticator_class': 'cs3api4lab.auth.RevaTokenAuth',
            'client_token': token_from_cs3
        }

        token_authenticator = Auth.get_authenticator(token_config, log=self.log)
        token = token_authenticator.authenticate('einstein')

        self.assertEqual(token_from_cs3, token)

    def test_authenticate_expire_riva_token(self):
        token_config = {
            'authenticator_class': 'cs3api4lab.auth.RevaTokenAuth',
            'client_token': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJyZXZhIiwiZXhwIjoxNjAyMTQ1NjU0LCJpYXQiOjE2MDIwNTkyNTQsImlzcyI6ImNlcm5ib3guY2Vybi5jaCIsInVzZXIiOnsiaWQiOnsiaWRwIjoiY2VybmJveC5jZXJuLmNoIiwib3BhcXVlX2lkIjoiNGM1MTBhZGEtYzg2Yi00ODE1LTg4MjAtNDJjZGY4MmMzZDUxIn0sInVzZXJuYW1lIjoiZWluc3RlaW4iLCJtYWlsIjoiZWluc3RlaW5AY2Vybi5jaCIsImRpc3BsYXlfbmFtZSI6IkFsYmVydCBFaW5zdGVpbiIsImdyb3VwcyI6WyJzYWlsaW5nLWxvdmVycyIsInZpb2xpbi1oYXRlcnMiLCJwaHlzaWNzLWxvdmVycyJdfX0.g58Ll4MtpzvrZ5K8IqiMtUgy8gZgAfUDzl2r0e2vukc"
        }

        token_authenticator = Auth.get_authenticator(token_config, log=self.log)
        with self.assertRaises(web.HTTPError):
            token_authenticator.authenticate('einstein')

    def test_authenticate_eos_token(self):
        token_config = {
            'authenticator_class': 'cs3api4lab.auth.eos.Eos',
            'eos_token': "oauth2:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJyZXZhIiwiZXhwIjoxNjAyMTQ1NjU0LCJpYXQiOjE2MDIwNTkyNTQsImlzcyI6ImNlcm5ib3guY2Vybi5jaCIsInVzZXIiOnsiaWQiOnsiaWRwIjoiY2VybmJveC5jZXJuLmNoIiwib3BhcXVlX2lkIjoiNGM1MTBhZGEtYzg2Yi00ODE1LTg4MjAtNDJjZGY4MmMzZDUxIn0sInVzZXJuYW1lIjoiZWluc3RlaW4iLCJtYWlsIjoiZWluc3RlaW5AY2Vybi5jaCIsImRpc3BsYXlfbmFtZSI6IkFsYmVydCBFaW5zdGVpbiIsImdyb3VwcyI6WyJzYWlsaW5nLWxvdmVycyIsInZpb2xpbi1oYXRlcnMiLCJwaHlzaWNzLWxvdmVycyJdfX0.g58Ll4MtpzvrZ5K8IqiMtUgy8gZgAfUDzl2r0e2vukc:<OAUTH_INSPECTION_ENDPOINT>"
        }

        token_authenticator = Auth.get_authenticator(token_config, log=self.log)
        token = token_authenticator.authenticate('einstein')
        self.assertEqual('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJyZXZhIiwiZXhwIjoxNjAyMTQ1NjU0LCJpYXQiOjE2MDIwNTkyNTQsImlzcyI6ImNlcm5ib3guY2Vybi5jaCIsInVzZXIiOnsiaWQiOnsiaWRwIjoiY2VybmJveC5jZXJuLmNoIiwib3BhcXVlX2lkIjoiNGM1MTBhZGEtYzg2Yi00ODE1LTg4MjAtNDJjZGY4MmMzZDUxIn0sInVzZXJuYW1lIjoiZWluc3RlaW4iLCJtYWlsIjoiZWluc3RlaW5AY2Vybi5jaCIsImRpc3BsYXlfbmFtZSI6IkFsYmVydCBFaW5zdGVpbiIsImdyb3VwcyI6WyJzYWlsaW5nLWxvdmVycyIsInZpb2xpbi1oYXRlcnMiLCJwaHlzaWNzLWxvdmVycyJdfX0.g58Ll4MtpzvrZ5K8IqiMtUgy8gZgAfUDzl2r0e2vukc', token)

    def test_authenticate_eos_file(self):
        path = Path(os.getcwd() + "/jupyter-config/eos_token.txt")
        token_config = {
            'authenticator_class': 'cs3api4lab.auth.eos.Eos',
            'eos_file': path
        }

        token_authenticator = Auth.get_authenticator(token_config, log=self.log)
        token = token_authenticator.authenticate('einstein')
        self.assertEqual('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJyZXZhIiwiZXhwIjoxNjAyMTQ1NjU0LCJpYXQiOjE2MDIwNTkyNTQsImlzcyI6ImNlcm5ib3guY2Vybi5jaCIsInVzZXIiOnsiaWQiOnsiaWRwIjoiY2VybmJveC5jZXJuLmNoIiwib3BhcXVlX2lkIjoiNGM1MTBhZGEtYzg2Yi00ODE1LTg4MjAtNDJjZGY4MmMzZDUxIn0sInVzZXJuYW1lIjoiZWluc3RlaW4iLCJtYWlsIjoiZWluc3RlaW5AY2Vybi5jaCIsImRpc3BsYXlfbmFtZSI6IkFsYmVydCBFaW5zdGVpbiIsImdyb3VwcyI6WyJzYWlsaW5nLWxvdmVycyIsInZpb2xpbi1oYXRlcnMiLCJwaHlzaWNzLWxvdmVycyJdfX0.g58Ll4MtpzvrZ5K8IqiMtUgy8gZgAfUDzl2r0e2vukc', token)
