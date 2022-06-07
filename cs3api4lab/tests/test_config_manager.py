import os
from unittest import TestCase

from cs3api4lab.config.config_manager import Config
from traitlets.config import LoggingConfigurable
from cs3api4lab.config.config_manager import Cs3ConfigManager


class TestCS3ConfigManager(TestCase):
    config = {
        'reva_host': '127.0.0.1:19000',
        'auth_token_validity': 3600,
        'endpoint': '/',
        'mount_dir': '/home',
        'home_dir': '',
        'root_dir_list': ('/home', '/reva'),
        'chunk_size': 4194304,
        'secure_channel': False,
        'client_cert': None,
        'client_key': None,
        'ca_cert': None,
        'login_type': 'basic',
        'authenticator_class': 'cs3api4lab.auth.RevaPassword',
        'client_id': 'einstein',
        'client_secret': 'relativity',
        'locks_expiration_time': 10,
        'tus_enabled': False,
        'enable_ocm': False,
        "shared_folder": "MyShares",
        "kernel_path": "/"
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
        configManager = Cs3ConfigManager().get_config()

        self.assertEqual(configManager.reva_host, self.config["reva_host"])
        self.assertEqual(configManager.client_id, self.config["client_id"])
        self.assertEqual(configManager.client_secret, self.config["client_secret"])
        self.assertEqual(configManager.auth_token_validity, self.config["auth_token_validity"])
        self.assertEqual(configManager.endpoint, self.config["endpoint"])
        self.assertEqual(configManager.mount_dir, self.config["mount_dir"])
        self.assertEqual(configManager.root_dir_list, self.config["root_dir_list"])
        self.assertEqual(configManager.chunk_size, self.config["chunk_size"])
        self.assertEqual(configManager.secure_channel, self.config["secure_channel"])
        self.assertEqual(configManager.authenticator_class, self.config["authenticator_class"])
        self.assertEqual(configManager.login_type, self.config["login_type"])
        self.assertEqual(configManager.locks_expiration_time, int(self.config["locks_expiration_time"]))
        self.assertEqual(configManager.client_key, self.config["client_key"])
        self.assertEqual(configManager.client_cert, self.config["client_cert"])
        self.assertEqual(configManager.ca_cert, self.config["ca_cert"])
        self.assertEqual(configManager.tus_enabled, self.config["tus_enabled"])
        self.assertEqual(configManager.enable_ocm, self.config["enable_ocm"])
        self.assertEqual(configManager.shared_folder, self.config["shared_folder"])
        

    def test_load_from_environment_variables(self):
        os.environ['CS3_REVA_HOST'] = '1.2.3.4:5'
        os.environ['CS3_SECURE_CHANNEL'] = 'true'
        os.environ['CS3_CA_CERT'] = 'abcdf12345'
        os.environ['CS3_LOCKS_EXPIRATION_TIME'] = '123'
        os.environ['CS3_TUS_ENABLED'] = 'false'
        os.environ['CS3_ENABLE_OCM'] = 'false'

        configManager = Config()

        self.assertEqual(configManager.reva_host, '1.2.3.4:5')
        self.assertTrue(configManager.secure_channel)
        self.assertTrue(isinstance(configManager.secure_channel, bool))
        self.assertFalse(configManager.tus_enabled)
        self.assertTrue(isinstance(configManager.tus_enabled, bool))
        self.assertFalse(configManager.enable_ocm)
        self.assertTrue(isinstance(configManager.enable_ocm, bool))
        self.assertEqual(configManager.ca_cert, 'abcdf12345')
        self.assertEqual(int(configManager.locks_expiration_time), 123)
