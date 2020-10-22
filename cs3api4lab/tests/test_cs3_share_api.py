from unittest import TestCase
from unittest import skip
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from traitlets.config import LoggingConfigurable


class TestCs3ShareApi(TestCase, LoggingConfigurable):
    api = None
    config = None
    share_id = None

    receiver_id = 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c'
    receiver_idp = 'cesnet.cz'

    receiver2_id = '932b4540-8d16-481e-8ef4-588e4b6b151c'
    receiver2_idp = 'example.org'

    receiver_role = 'viewer'
    receiver_grantee_type = 'user'
    file_path = '/test.txt'
    storage_id = '123e4567-e89b-12d3-a456-426655440000'

    def setUp(self):
        self.config = Cs3ConfigManager.get_config()
        self.storage = Cs3FileApi(self.log)
        self.api = Cs3ShareApi(self.log)

    def test_create_and_list_directory_model(self):

        created_share = self._create_share()
        self.share_id = created_share['opaque_id']
        share_list = self.api.list_dir_model()

        try:
            if not list(filter(lambda s: s['path'] == str(self.file_path), share_list['content'])):
                raise Exception("Share not created")
        finally:
            self._clear_shares()

    def test_create_duplicate_and_list_directory_model(self):

        created_share = self._create_share()
        self.share_id = created_share['opaque_id']

        self._create_test_share(self.receiver2_id, self.receiver2_idp)

        share_list = self.api.list_dir_model()
        self.assertEqual(len(share_list['content']), 1)

        try:
            if not list(filter(lambda s: s['path'] == str(self.file_path), share_list['content'])):
                raise Exception("Share not created")
        finally:
            self._clear_shares()

    def test_create_and_list_directory_model(self):

        self._clear_shares()

        created_share = self._create_share()
        self.share_id = created_share['opaque_id']
        share_list = self.api.list_dir_model()

        try:
            if not list(filter(lambda s: s['path'] == str(self.file_path), share_list['content'])):
                raise Exception("Share not created")
        finally:
            self._clear_shares()

    def test_create_duplicate_and_list_directory_model(self):

        created_share = self._create_share()
        self.share_id = created_share['opaque_id']

        self._create_test_share(self.receiver2_id, self.receiver2_idp)

        share_list = self.api.list_dir_model()
        self.assertEqual(len(share_list['content']), 1)

        try:
            if not list(filter(lambda s: s['path'] == str(self.file_path), share_list['content'])):
                raise Exception("Share not created")
        finally:
            self._clear_shares()

    def test_list_grantees_for_file(self):
        self._create_share()
        response = self.api.list_grantees_for_file(self.file_path)
        try:
            if not response:
                raise Exception("Failed to retrieve grantees of the file")
            if response['shares'][0]['grantee']['opaque_id'] != self.receiver_id:
                raise Exception("Incorrect grantee")
            if response['shares'][0]['grantee']['permissions'] != self.receiver_role:
                raise Exception("Incorrect permissions")
        finally:
            self._clear_shares()

    def test_remove(self):
        created_share = self._create_share()
        self.share_id = created_share['opaque_id']
        share_list = self.api.list_dir_model()
        try:
            if not list(filter(lambda s: s['path'] == self.file_path, share_list['content'])):
                raise Exception("Share not created")
        finally:
            self.api.remove(self.share_id)
        share_list = self.api.list_dir_model()
        if list(filter(lambda s: s['path'] == self.file_path, share_list['content'])):
            raise Exception("Share not removed")

    def test_update(self):
        created_share = self._create_share()
        self.share_id = created_share['opaque_id']
        self.api.update(self.share_id, 'editor')
        share_list = self.api.list_grantees_for_file(self.file_path)
        try:
            if not list(filter(
                    lambda s: s['grantee']['opaque_id'] == self.receiver_id
                              and s['grantee']['permissions'] == 'editor',
                    share_list['shares'])):
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
        shares = self.api.list_grantees_for_file(self.file_path)
        for share in shares['shares']:
            self._remove_test_share(share['opaque_id'])
        try:
            self._remove_test_file()
        except IOError as e:
            print("Error remove file:", e)

    def _create_test_share(self, receiver_id='f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c', receiver_idp='cesnet.cz'):
        file_path = self.config['home_dir'] + self.file_path
        return self.api.create(self.config['endpoint'],
                               file_path,
                               receiver_id,
                               receiver_idp,
                               self.receiver_role,
                               self.receiver_grantee_type)

    def _remove_test_share(self, share_id):
        self.api.remove(share_id)

    def _create_test_file(self):
        self.storage.write_file(self.file_path,
                                self.config['client_id'],
                                "Lorem ipsum dolor sit amet...",
                                self.config['endpoint'])

    def _remove_test_file(self):
        self.storage.remove(self.file_path,
                            self.config['client_id'],
                            self.config['endpoint'])
