from unittest import TestCase, skip
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from traitlets.config import LoggingConfigurable
from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi

class TestCs3OCMShareApi(TestCase):
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
        self.log = LoggingConfigurable().log
        self.config = Cs3ConfigManager.get_config()
        self.storage = Cs3FileApi(self.log)
        self.api = Cs3OcmShareApi(self.log)

    def test_create_ocm_share(self):
        created_share = self._create_share()
        self.share_id = created_share['id']
        try:
            if self.api.get(self.share_id)['id'] is None:
                raise Exception("Share not created")
        finally:
            self._clear_shares()

    def test_update_ocm_share_permissions(self):
        created_share = self._create_share()
        self.share_id = created_share['id']
        try:
            self.api.update(self.share_id, 'permissions', ['editor', True])
            share = self.api.get(self.share_id)
            self.assertEqual(share['permissions'], 'editor', 'Change permission for ocm share failed')
        finally:
            self._clear_shares()

    def test_ocm_share_remove(self):
        created_share = self._create_share()
        self.share_id = created_share['id']
        try:
            self.api.remove(self.share_id)

            with self.assertRaises(Exception) as context:
                self.api.get(self.share_id)

            self.assertIn("Incorrect server response:", context.exception.args[0])
        finally:
            self._remove_test_file()

    def test_list_ocm_shares(self):
        created_share = self._create_share()
        self.share_id = created_share['id']
        try:
            share_list = self.api.list()
            self.assertTrue(
                list(share for share in share_list.shares if share.id.opaque_id == self.share_id),
                "Share not present")
        finally:
            self._clear_shares()

    def _create_share(self):
        self._create_test_file()
        return self._create_test_share()

    def _clear_shares(self):
        try:
            self.api.remove(self.share_id)
            self._remove_test_file()
        except IOError as e:
            print("Error remove file:", e)

    def _create_test_share(self, receiver_id='f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c', receiver_idp='cesnet.cz'):
        file_path = self.config.mount_dir + self.file_path
        return self.api.create(receiver_id,
                               receiver_idp,
                               receiver_idp,
                               self.config.endpoint,
                               file_path, self.receiver_grantee_type,
                               self.receiver_role, True)

    def _remove_test_share(self, share_id):
        self.api.remove(share_id)

    def _create_test_file(self):
        self.storage.write_file(self.file_path,
                                "Lorem ipsum dolor sit amet...",
                                self.config.endpoint)

    def _remove_test_file(self):
        self.storage.remove(self.file_path,
                            self.config.endpoint)
