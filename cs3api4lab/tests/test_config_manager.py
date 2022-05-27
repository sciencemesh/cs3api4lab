import os
from unittest import TestCase

from cs3api4lab.config.config_manager import Config
from traitlets.config import LoggingConfigurable
from cs3api4lab.config.config_manager import Cs3ConfigManager


class TestCS3ConfigManager(TestCase):
    config = {
        'reva_host': '127.0.0.1:19000',
        'auth_token_validity': '3600',
        'endpoint': '/',
        'home_dir': '/home',
        'root_dir_list': ('/home', '/reva'),
        'chunk_size': '4194304',
        'secure_channel': False,
        'client_cert': '',
        'client_key': '',
        'ca_cert': '',
        'login_type': 'basic',
        'authenticator_class': 'cs3api4lab.auth.RevaPassword',
        'client_id': 'einstein',
        'client_secret': 'relativity',
        'locks_expiration_time': 10,
        'tus_enabled': False,
        'enable_ocm': False,
        "shared_folder": "MyShares"
    }

    @classmethod
    def tearDownClass(cls):
        Cs3ConfigManager.clean()

    def setUp(self):
        self.log = LoggingConfigurable().log

        for env in os.environ:
            if env.startswith('CS3_'):
                del os.environ[env]


    def test_load_config_file_for_tests(self):
        configManager = Config()

        self.assertDictEqual(configManager.config, self.config)

    def test_load_from_environment_variables(self):
        os.environ['CS3_reva_host'] = '1.2.3.4:5'
        os.environ['CS3_secure_channel'] = 'true'
        os.environ['CS3_ca_cert'] = 'abcdf12345'
        os.environ['CS3_locks_expiration_time'] = '123'
        os.environ['CS3_tus_enabled'] = 'false'
        os.environ['CS3_enable_ocm'] = 'false'

        configManager = Config()

        self.assertEqual(configManager.config['reva_host'], '1.2.3.4:5')
        self.assertTrue(configManager.config['secure_channel'])
        self.assertTrue(isinstance(configManager.config['secure_channel'], bool))
        self.assertFalse(configManager.config['tus_enabled'])
        self.assertTrue(isinstance(configManager.config['tus_enabled'], bool))
        self.assertFalse(configManager.config['enable_ocm'])
        self.assertTrue(isinstance(configManager.config['enable_ocm'], bool))
        self.assertEqual(configManager.config['ca_cert'], 'abcdf12345')
        self.assertEqual(int(configManager.config['locks_expiration_time']), 123)
