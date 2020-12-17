from unittest import TestCase
from cs3api4lab.api.cs3_public_share_api import Cs3PublicShareApi
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from traitlets.config import LoggingConfigurable


class TestCs3PublicShareApi(TestCase, LoggingConfigurable):
    file_path = '/test.txt'
    config = None
    storage = None
    api = None

    def setUp(self):
        self.config = Cs3ConfigManager.get_config()
        self.storage = Cs3FileApi(self.log)
        self.api = Cs3PublicShareApi(self.log)

    def test_create_public_share(self):
        share = self._create_public_share()
        assert share['opaque_id'] is not None
        assert share['token'] is not None
        self._delete_public_share(share['opaque_id'])

    def test_get_public_share(self):
        self._create_test_file()
        share = self._create_public_share()
        opaque_id = share['opaque_id']
        token = share['token']
        share_got = self.api.get_public_share(opaque_id, token)
        assert share['opaque_id'] == share_got['opaque_id']
        assert share['token'] == share_got['token']
        self._delete_public_share(share['opaque_id'])

    def test_get_public_share_by_token(self):
        self._create_test_file()
        share = self._create_public_share()
        token = share['token']
        share_got = self.api.get_public_share_by_token(token, 'pass')
        assert share['opaque_id'] == share_got['opaque_id']
        assert share['token'] == share_got['token']
        self._delete_public_share(share['opaque_id'])

    def test_remove_public_share(self):
        self._create_test_file()
        share = self._create_public_share()
        token = share['token']
        share_got = self.api.get_public_share_by_token(token, 'pass')
        assert share['opaque_id'] == share_got['opaque_id']
        self.api.remove_public_share(share['opaque_id'])
        try:
            self.api.get_public_share_by_token(token, '')
        except Exception as e:
            self._remove_test_file()
        else:
            assert False

    def test_update_public_share_date(self):
        self._create_test_file()
        share = self._create_public_share()
        new_date = '12-12-2060'
        self.api.update_public_share(share['opaque_id'],
                                     share['token'],
                                     'exp_date',
                                     new_date)
        updated_share = self.api.get_public_share_by_token(share['token'], 'pass')
        assert updated_share['expiration'] == new_date
        self._delete_public_share(share['opaque_id'])

    def test_update_public_share_display_name(self):
        self._create_test_file()
        share = self._create_public_share()
        new_display_name = 'new_name'
        self.api.update_public_share(share['opaque_id'],
                                     share['token'],
                                     'display_name',
                                     new_display_name)
        updated_share = self.api.get_public_share_by_token(share['token'], 'pass')
        assert updated_share['display_name'] == new_display_name
        self._delete_public_share(share['opaque_id'])

    def test_update_public_share_password(self):
        self._create_test_file()
        share = self._create_public_share()
        new_password = 'superpassword'
        self.api.update_public_share(share['opaque_id'],
                                     share['token'],
                                     'password',
                                     new_password)
        updated_share = self.api.get_public_share_by_token(share['token'], new_password)
        assert share['opaque_id'] == updated_share['opaque_id']
        self._delete_public_share(share['opaque_id'])

    def test_update_public_share_permissions(self):
        self._create_test_file()
        share = self._create_public_share()
        new_perms = {'add_grant': True,
                     'delete': True}
        self.api.update_public_share(share['opaque_id'],
                                     share['token'],
                                     'permissions',
                                     new_perms)
        updated_share = self.api.get_public_share_by_token(share['token'], 'pass')
        assert updated_share['permissions']['add_grant'] is True
        assert updated_share['permissions']['delete'] is True
        self._delete_public_share(share['opaque_id'])

    def test_list_public_shares(self):
        self._create_test_file()
        share = self._create_public_share()
        shares = self.api.list_public_shares()
        try:
            if not list(filter(lambda s: s['opaque_id'] == share['opaque_id'], shares)):
                raise Exception("Public share not created")
        finally:
            self._delete_public_share(share['opaque_id'])

    def _create_public_share(self):
        self._create_test_file()
        return self.api.create_public_share(self.config['endpoint'],
                                            self.file_path,
                                            'pass',
                                            '31-12-2030',
                                            None)

    def _delete_public_share(self, opaque_id):
        self.api.remove_public_share(opaque_id)
        self._remove_test_file()

    def _remove_test_file(self):
        self.storage.remove(self.file_path,
                            self.config['endpoint'])

    def _create_test_file(self):
        self.storage.write_file(self.file_path,
                                "Lorem ipsum dolor sit amet...",
                                self.config['endpoint'])
