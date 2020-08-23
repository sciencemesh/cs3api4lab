from unittest import TestCase
from cs3api_test_ext.cs3_share_api import Cs3ShareApi


class TestCs3ShareApi(TestCase):
    api = Cs3ShareApi()
    config = {
        "file_path": "/share_api_test_file.txt",
        "user_id": "f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c",
        "user_idp": "cesnet.cz",
        "user_role": "viewer",
        "grantee_type": "user"
    }

    def test_create_and_list(self):
        created_share = self._create_test_share()
        share_id = created_share['opaque_id']
        share_list = self.api.list()
        try:
            if not list(filter(lambda s: s['opaque_id'] == str(share_id), share_list)):
                raise Exception("Share not created")
        finally:
            self._remove_test_share(share_id)

    def test_list_grantees_for_file(self):
        created_share = self._create_test_share()
        shares_dict = self.api.list_grantees_for_file(self.config['file_path'])
        try:
            if not shares_dict:
                raise Exception("Failed to retrieve grantees of the file")
            if shares_dict[self.config['user_id']] is not self.config['user_role']:
                raise Exception("Incorrect grantee")
        finally:
            self._remove_test_share(created_share['opaque_id'])

    def test_remove(self):
        created_share = self._create_test_share()
        share_id = created_share['opaque_id']
        share_list = self.api.list()
        try:
            if not list(filter(lambda s: s['opaque_id'] == str(share_id), share_list)):
                raise Exception("Share not created")
        finally:
            self.api.remove(share_id)
        share_list = self.api.list()
        if list(filter(lambda s: s['opaque_id'] == str(share_id), share_list)):
            raise Exception("Share not removed")

    def test_update(self):
        created_share = self._create_test_share()
        share_id = created_share['opaque_id']
        self.api.update(share_id, 'editor')
        share_list = self.api.list()
        try:
            if not list(filter(
                    lambda s: s['opaque_id'] == str(share_id) and s['permissions'] == 'editor',
                    share_list)):
                raise Exception("Share not updated")
        finally:
            self.api.remove(share_id)

    # def test_list_received(self):
    #     self.api.list_received()
    #
    # def test_update_received(self):
    #     self.api.update_received("1", "accepted")

    def _create_test_share(self):
        return self.api.create("/",
                               self.config['file_path'],
                               self.config['user_id'],
                               self.config['user_idp'],
                               self.config['user_role'],
                               self.config['grantee_type'])

    def _remove_test_share(self, share_id):
        self.api.remove(share_id)
