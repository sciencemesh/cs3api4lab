from unittest import TestCase

from cs3api4lab.api.cs3_user_api import Cs3UserApi
from traitlets.config import LoggingConfigurable


class TestCs3UserApi(TestCase):

    def setUp(self):
        self.log = LoggingConfigurable().log
        self.user_api = Cs3UserApi(self.log)

    def test_get_user_info(self):
        opaque_id = "4c510ada-c86b-4815-8820-42cdf82c3d51"
        idp = "cernbox.cern.ch"

        expected_info = {"username": "einstein",
                    "display_name": "Albert Einstein",
                    "full_name": "Albert Einstein (einstein)",
                    "idp": "cernbox.cern.ch",
                    "opaque_id": "4c510ada-c86b-4815-8820-42cdf82c3d51",
                    "mail": "einstein@cern.ch"}

        user_info = self.user_api.get_user_info(idp, opaque_id)
        self.assertDictEqual(user_info, expected_info)

    def test_get_user_info_non_existing_id(self):
        opaque_id = "non-existing"
        idp = "cernbox.cern.ch"

        user_info = self.user_api.get_user_info(idp, opaque_id)

        self.assertFalse(user_info)

    def test_get_user_info_empty_id(self):
        opaque_id = ""
        idp = "cernbox.cern.ch"

        user_info = self.user_api.get_user_info(idp, opaque_id)

        self.assertFalse(user_info)

    def test_get_user_by_claim(self):
        claim = "mail"
        value = "einstein@cern.ch"

        expected_info = {"username": "einstein",
                    "display_name": "Albert Einstein",
                    "full_name": "Albert Einstein (einstein)",
                    "idp": "cernbox.cern.ch",
                    "opaque_id": "4c510ada-c86b-4815-8820-42cdf82c3d51",
                    "mail": "einstein@cern.ch"}

        user_info = self.user_api.get_user_info_by_claim(claim, value)

        self.assertDictEqual(user_info, expected_info)

    def test_find_users_by_query(self):
        query = 'einstein'

        expected_info = {"username": "einstein",
                    "display_name": "Albert Einstein",
                    "full_name": "Albert Einstein (einstein)",
                    "idp": "cernbox.cern.ch",
                    "opaque_id": "4c510ada-c86b-4815-8820-42cdf82c3d51",
                    "mail": "einstein@cern.ch"}

        user = self.user_api.find_users_by_query(query)
        self.assertTrue(user)

        user_info = user[0]
        self.assertDictEqual(user_info, expected_info)

    def test_find_users_by_query_less_than_three_chars(self):
        query = ''
        self.assertFalse(self.user_api.find_users_by_query(query))

        query = 'e'
        self.assertFalse(self.user_api.find_users_by_query(query))

        query = 'ei'
        self.assertFalse(self.user_api.find_users_by_query(query))

    def test_find_users_by_query_three_chars(self):
        query = 'ein'

        expected_info = {"username": "einstein",
                    "display_name": "Albert Einstein",
                    "full_name": "Albert Einstein (einstein)",
                    "idp": "cernbox.cern.ch",
                    "opaque_id": "4c510ada-c86b-4815-8820-42cdf82c3d51",
                    "mail": "einstein@cern.ch"}

        user = self.user_api.find_users_by_query(query)
        self.assertTrue(user)

        user_info = user[0]
        self.assertDictEqual(user_info, expected_info)
