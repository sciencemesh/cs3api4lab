from datetime import datetime
import os
from pathlib import Path
from unittest import TestCase, skip

import jwt
from tornado import web
from traitlets.config import LoggingConfigurable

from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.reva_password import RevaPassword
from cs3api4lab.config.config_manager import Cs3ConfigManager


class TestAuthenticator(TestCase):

    def setUp(self) -> None:
        Auth.clean()
        Cs3ConfigManager.clean()
        self.log = LoggingConfigurable().log

    @classmethod
    def tearDownClass(cls):
        Auth.clean()
        Cs3ConfigManager.clean()

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
        token = authenticator.authenticate()
        tokens = token.split('.')
        self.assertEqual(len(tokens), 3)

        decode = jwt.decode(jwt=token, algorithms=["HS256"], options={"verify_signature": False})
        self.assertEqual(decode['aud'], 'reva')
        self.assertIsNotNone(decode['exp'])
        self.assertIsNotNone(decode['iat'])
        self.assertIsNotNone(decode['iss'])
        self.assertEqual(decode['user']['id']['idp'], 'cernbox.cern.ch')
        self.assertEqual(decode['user']['id']['opaque_id'], '4c510ada-c86b-4815-8820-42cdf82c3d51')
        self.assertEqual(decode['user']['username'], 'einstein')
        self.assertEqual(decode['user']['mail'], 'einstein@cern.ch')
        self.assertEqual(decode['user']['display_name'], 'Albert Einstein')
        self.assertEqual(len(tokens), 3)

    @skip
    def test_authenticate_eos_token(self):
        oauth_token = self._create_oauth_token()

        token_config = {
            'authenticator_class': 'cs3api4lab.auth.Eos',
            'eos_token': f"oauth2:{oauth_token}:<OAUTH_INSPECTION_ENDPOINT>"
        }

        token_authenticator = Auth.get_authenticator(token_config, log=self.log)
        token = token_authenticator.authenticate()
        tokens = token.split('.')
        self.assertEqual(len(tokens), 3)
        decode = jwt.decode(jwt=token, verify=False)
        self.assertEqual(decode['aud'], 'reva')
        self.assertIsNotNone(decode['exp'])
        self.assertIsNotNone(decode['iat'])
        self.assertIsNotNone(decode['iss'])

    def test_authenticate_expire_eos_token(self):
        token_config = {
            'authenticator_class': 'cs3api4lab.auth.Eos',
            'client_id': 'einstein',
            'eos_token': "oauth2:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJyZXZhIiwiZXhwIjoxNjAyMTQ1NjU0LCJpYXQiOjE2MDIwNTkyNTQsImlzcyI6ImNlcm5ib3guY2Vybi5jaCIsInVzZXIiOnsiaWQiOnsiaWRwIjoiY2VybmJveC5jZXJuLmNoIiwib3BhcXVlX2lkIjoiNGM1MTBhZGEtYzg2Yi00ODE1LTg4MjAtNDJjZGY4MmMzZDUxIn0sInVzZXJuYW1lIjoiZWluc3RlaW4iLCJtYWlsIjoiZWluc3RlaW5AY2Vybi5jaCIsImRpc3BsYXlfbmFtZSI6IkFsYmVydCBFaW5zdGVpbiIsImdyb3VwcyI6WyJzYWlsaW5nLWxvdmVycyIsInZpb2xpbi1oYXRlcnMiLCJwaHlzaWNzLWxvdmVycyJdfX0.g58Ll4MtpzvrZ5K8IqiMtUgy8gZgAfUDzl2r0e2vukc:<OAUTH_INSPECTION_ENDPOINT>"
        }

        with self.assertRaises(web.HTTPError):
            token_authenticator = Auth.get_authenticator(token_config, log=self.log)
            token_authenticator.authenticate()

    def test_authenticate_expire_eos_file(self):
        path = Path(os.getcwd() + "/jupyter-config/eos_token.txt") #might be cs3api4lab/cs3api4lab/tests/... depending on the environment setup
        token_config = {
            'authenticator_class': 'cs3api4lab.auth.Eos',
            'client_id': 'einstein',
            'eos_file': path
        }

        with self.assertRaises(web.HTTPError):
            token_authenticator = Auth.get_authenticator(token_config, log=self.log)
            token_authenticator.authenticate()

    def test_authenticate_non_eos_file(self):
        path = Path(os.getcwd() + "/jupyter-config/non_exits.txt")
        token_config = {
            'authenticator_class': 'cs3api4lab.auth.Eos',
            'eos_file': path
        }

        with self.assertRaises(IOError):
            token_authenticator = Auth.get_authenticator(token_config, log=self.log)
            token_authenticator.authenticate()

    def test_authenticate_expire_oauth_token(self):
        token_config = {
            'authenticator_class': 'cs3api4lab.auth.Oauth',
            'client_id': 'einstein',
            'oauth_token': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJyZXZhIiwiZXhwIjoxNjAyMTQ1NjU0LCJpYXQiOjE2MDIwNTkyNTQsImlzcyI6ImNlcm5ib3guY2Vybi5jaCIsInVzZXIiOnsiaWQiOnsiaWRwIjoiY2VybmJveC5jZXJuLmNoIiwib3BhcXVlX2lkIjoiNGM1MTBhZGEtYzg2Yi00ODE1LTg4MjAtNDJjZGY4MmMzZDUxIn0sInVzZXJuYW1lIjoiZWluc3RlaW4iLCJtYWlsIjoiZWluc3RlaW5AY2Vybi5jaCIsImRpc3BsYXlfbmFtZSI6IkFsYmVydCBFaW5zdGVpbiIsImdyb3VwcyI6WyJzYWlsaW5nLWxvdmVycyIsInZpb2xpbi1oYXRlcnMiLCJwaHlzaWNzLWxvdmVycyJdfX0.g58Ll4MtpzvrZ5K8IqiMtUgy8gZgAfUDzl2r0e2vukc"
        }

        with self.assertRaises(web.HTTPError):
            token_authenticator = Auth.get_authenticator(token_config, log=self.log)
            token_authenticator.authenticate()

    @staticmethod
    def _create_oauth_token():
        now = datetime.timestamp(datetime.now())

        payload = {
            'exp': now + 3600,
            'iat': now,
            'iss': 'cernbox.cern.ch',
            'user': {
                'id': {'idp': 'cernbox.cern.ch',
                       'opaque_id': '4c510ada-c86b-4815-8820-42cdf82c3d51'},
                'username': 'einstein',
                'mail': 'einstein@cern.ch',
                'display_name': 'Albert Einstein',
                'groups': ['sailing-lovers', 'violin-haters', 'physics-lovers']
            }}

        token = jwt.encode(payload=payload, key="Pive-Fumkiu4")
        return token.decode("utf-8")
