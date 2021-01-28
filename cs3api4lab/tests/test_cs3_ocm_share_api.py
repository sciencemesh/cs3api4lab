from unittest import TestCase
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from traitlets.config import LoggingConfigurable
from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi


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
        self.api = Cs3OcmShareApi(self.log)

    def test_create_ocm_share(self):
        created_share = self._create_share()
        self.share_id = created_share['id']
        try:
            if self.api.get_ocm_shares(self.share_id)['id'] is None:
                raise Exception("Share not created")
        finally:
            self._clear_shares()

    def test_update_ocm_share_permissions(self):
        created_share = self._create_share()
        self.share_id = created_share['id']
        try:
            self.api.update_ocm_share(self.share_id, 'permissions', ['editor', True])
            if self.api.get_ocm_shares(self.share_id)['permissions'] != 'editor':
                raise Exception("Permissions not updated")
        finally:
            self._clear_shares()

    def test_ocm_share_remove(self):
        created_share = self._create_share()
        self.share_id = created_share['id']
        try:
            if self.api.get_ocm_shares(self.share_id)['id'] == '':
                raise Exception("Share not created")
            self.api.remove_ocm_share(self.share_id)
            if self.api.get_ocm_shares(self.share_id)['id'] != '':
                raise Exception("Share not removed")
        finally:
            self._remove_test_file()

    def test_list_ocm_shares(self):
        created_share = self._create_share()
        self.share_id = created_share['id']
        try:
            share = self.api.get_ocm_shares(share_id=self.share_id)
            if share['id'] != self.share_id:
                raise Exception("Shares not listed")
        finally:
            self._clear_shares()

    def _create_share(self):
        self._create_test_file()
        return self._create_test_share()

    def _clear_shares(self):
        try:
            self.api.remove_ocm_share(self.share_id)
            self._remove_test_file()
        except IOError as e:
            print("Error remove file:", e)

    def _create_test_share(self, receiver_id='f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c', receiver_idp='cesnet.cz'):
        file_path = self.config['home_dir'] + self.file_path
        return self.api.create_ocm_share(receiver_id,
                                         receiver_idp,
                                         receiver_idp,
                                         self.config['endpoint'],
                                         file_path, self.receiver_grantee_type,
                                         self.receiver_role, True)

    def _remove_test_share(self, share_id):
        self.api.remove_ocm_share(share_id)

    def _create_test_file(self):
        self.storage.write_file(self.file_path,
                                "Lorem ipsum dolor sit amet...",
                                self.config['endpoint'])

    def _remove_test_file(self):
        self.storage.remove(self.file_path,
                            self.config['endpoint'])
