import random
import string

from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi
from cs3api4lab.api.share_api_facade import ShareAPIFacade

from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.logic.storage_logic import StorageLogic
from cs3api4lab.tests.extensions import *


class ShareTestBase:
    def setUp(self):
        config = Cs3ConfigManager().get_config()
        self.file_api = Cs3FileApi(self.log)
        self.share_api = Cs3ShareApi(self.log)
        self.ocm_api = Cs3OcmShareApi(self.log)
        self.uni_api = ShareAPIFacade(self.log)
        self.auth = ExtAuthenticator(config, self.log)
        self.storage_logic = StorageLogic(self.log)

        marie_ext_config = {
            "reva_host": "127.0.0.1:29000",
            "auth_token_validity": "3600",
            "endpoint": "/",
            "home_dir": "/home",
            "chunk_size": "4194304",
            "secure_channel": False,
            "client_cert": "",
            "client_key": "",
            "ca_cert": "",
            "authenticator_class": "cs3api4lab.auth.RevaPassword",
            "client_id": "marie",
            "client_secret": "radioactivity",
	        "locks_expiration_time": 10
            }
        richard_local_config = {
            "reva_host": "127.0.0.1:19000",
            "auth_token_validity": "3600",
            "endpoint": "/",
            "home_dir": "/home",
            "chunk_size": "4194304",
            "secure_channel": False,
            "client_cert": "",
            "client_key": "",
            "ca_cert": "",
            "authenticator_class": "cs3api4lab.auth.RevaPassword",
            "client_id": "richard",
            "client_secret": "superfluidity",
	        "locks_expiration_time": 10
        }
        self.marie_uni_api = ExtCs3ShareApiFacade(self.log, marie_ext_config)
        self.marie_file_api = ExtCs3FileApi(self.log, marie_ext_config)
        self.marie_share_api = ExtCs3ShareApi(self.log, marie_ext_config)
        self.marie_ocm_share_api = ExtCs3OcmShareApi(self.log, marie_ext_config)

        self.richard_uni_api = ExtCs3ShareApiFacade(self.log, richard_local_config)
        self.richard_file_api = ExtCs3FileApi(self.log, richard_local_config)
        self.richard_share_api = ExtCs3ShareApi(self.log, richard_local_config)
        self.richard_ocm_share_api = ExtCs3OcmShareApi(self.log, richard_local_config)

    def read_file_content(self, file_api, file_path):
        content = ''
        for chunk in file_api.read_file(file_path):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            content += chunk.decode('utf-8')
        return content

    def create_ocm_share(self, user, ocm_receiver_id, ocm_receiver_idp, file_path):
        self.create_test_file(user, file_path)
        if user == 'einstein':
            return self.ocm_api.create(ocm_receiver_id,
                                       ocm_receiver_idp,
                                       ocm_receiver_idp,
                                       self.storage_id, file_path)
        if user == 'marie':
            return self.marie_ocm_share_api.create(ocm_receiver_id,
                                                   ocm_receiver_idp,
                                                   ocm_receiver_idp,
                                                   self.storage_id, file_path)
        if user == 'richard':
            return self.richard_ocm_share_api.create(ocm_receiver_id,
                                                     ocm_receiver_idp,
                                                     ocm_receiver_idp,
                                                     self.storage_id, file_path)

    def create_share(self, user, receiver_id, receiver_idp, file_path):
        self.create_test_file(user, file_path)
        if user == 'einstein':
            return self.share_api.create(self.storage_id,
                                         file_path,
                                         receiver_id,
                                         receiver_idp,
                                         self.receiver_role,
                                         self.receiver_grantee_type)
        if user == 'marie':
            return self.marie_share_api.create(self.storage_id,
                                               file_path,
                                               receiver_id,
                                               receiver_idp,
                                               self.receiver_role,
                                               self.receiver_grantee_type)
        if user == 'richard':
            return self.richard_share_api.create(self.storage_id,
                                                 file_path,
                                                 receiver_id,
                                                 receiver_idp,
                                                 self.receiver_role,
                                                 self.receiver_grantee_type)

    def remove_test_share(self, user, share_id):
        if user == 'einstein':
            self.share_api.remove(share_id)
        if user == 'marie':
            self.marie_share_api.remove(share_id)
        if user == 'richard':
            self.richard_share_api.remove(share_id)

    def remove_test_ocm_share(self, user, share_id):
        if user == 'einstein':
            self.ocm_api.remove(share_id)
        if user == 'marie':
            self.marie_ocm_share_api.remove(share_id)
        if user == 'richard':
            self.richard_ocm_share_api.remove(share_id)

    def create_test_file(self, user, file_path):
        if user == 'einstein':
            self.file_api.write_file(file_path,
                                     "Lorem ipsum dolor sit amet...",
                                     self.storage_id)
        if user == 'marie':
            self.marie_file_api.write_file(file_path,
                                           "Lorem ipsum dolor sit amet...",
                                           self.storage_id)
        if user == 'richard':
            self.richard_file_api.write_file(file_path,
                                             "Lorem ipsum dolor sit amet...",
                                             self.storage_id)

    def remove_test_file(self, user, file_path):
        if user == 'einstein':
            self.file_api.remove(file_path, self.storage_id)
        if user == 'marie':
            self.marie_file_api.remove(file_path, self.storage_id)
        if user == 'richard':
            self.richard_file_api.remove(file_path, self.storage_id)

    def get_random_suffix(self):
        return '-' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))