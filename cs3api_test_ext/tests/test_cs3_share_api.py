from unittest import TestCase
from unittest import skip
from cs3api_test_ext.api.cs3_share_api import Cs3ShareApi
from cs3api_test_ext.api.cs3_file_api import Cs3FileApi
from cs3api_test_ext.config.config_manager import ConfigManager
from traitlets.config import LoggingConfigurable


class TestCs3ShareApi(TestCase, LoggingConfigurable):
    api = None
    config = {}
    share_id = None

    def setUp(self):
        self.config = ConfigManager('test.conf').config
        self.storage = Cs3FileApi(self.config, self.log)
        self.api = Cs3ShareApi(self.config)

    def test_create_and_list(self):
        created_share = self._create_share()
        self.share_id = created_share['opaque_id']
        share_list = self.api.list()
        try:
            if not list(filter(lambda s: s['opaque_id'] == str(self.share_id), share_list)):
                raise Exception("Share not created")
        finally:
            self._clear_shares()

    def test_list_grantees_for_file(self):
        self._create_share()
        shares_dict = self.api.list_grantees_for_file(self.config['file_path'])
        try:
            if not shares_dict:
                raise Exception("Failed to retrieve grantees of the file")
            if shares_dict[self.config['receiver_id']] != self.config['receiver_role']:
                raise Exception("Incorrect grantee")
        finally:
            self._clear_shares()

    def test_remove(self):
        created_share = self._create_share()
        self.share_id = created_share['opaque_id']
        share_list = self.api.list()
        try:
            if not list(filter(lambda s: s['opaque_id'] == str(self.share_id), share_list)):
                raise Exception("Share not created")
        finally:
            self.api.remove(self.share_id)
        share_list = self.api.list()
        if list(filter(lambda s: s['opaque_id'] == str(self.share_id), share_list)):
            raise Exception("Share not removed")

    def test_update(self):
        created_share = self._create_share()
        self.share_id = created_share['opaque_id']
        self.api.update(self.share_id, 'editor')
        share_list = self.api.list()
        try:
            if not list(filter(
                    lambda s: s['opaque_id'] == str(self.share_id) and s['permissions'] == 'editor',
                    share_list)):
                raise Exception("Share not updated")
        finally:
            self._clear_shares()

    @skip
    def test_list_received(self):
        self.api.list_received()

    @skip
    def test_update_received(self):
        self.api.update_received("1", "accepted")

    def _create_share(self):
        self._create_test_file()
        return self._create_test_share()

    def _clear_shares(self):
        shares = self.api.list()
        for share in shares:
            self._remove_test_share(share['opaque_id'])
        self._remove_test_file()

    def _create_test_share(self):
        file_path = self.config['home_dir'] + self.config['file_path']
        return self.api.create(self.config['endpoint'],
                               file_path,
                               self.config['receiver_id'],
                               self.config['receiver_idp'],
                               self.config['receiver_role'],
                               self.config['receiver_grantee_type'])

    def _remove_test_share(self, share_id):
        self.api.remove(share_id)

    def _create_test_file(self):
        self.storage.write_file(self.config['file_path'],
                                self.config['client_id'],
                                "Lorem ipsum dolor sit amet...",
                                self.config['endpoint'])

    def _remove_test_file(self):
        self.storage.remove(self.config['file_path'],
                            self.config['client_id'],
                            self.config['endpoint'])