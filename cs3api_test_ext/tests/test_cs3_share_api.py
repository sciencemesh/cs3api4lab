from unittest import TestCase

from cs3api_test_ext.cs3_share_api import Cs3ShareApi


class TestCs3ShareApi(TestCase):
    api = Cs3ShareApi()
    config = {
        "revahost": "127.0.0.1:19000",
        "authtokenvalidity": 3600,
        "userid": "einstein",
        "endpoint": "/",
        "chunksize": 4194304
    }

    def test_create(self):
        self.api.create("/", "/test.txt", "einstein", "marie")

    def test_list(self):
        self.api.list("einstein")

    def test_remove(self):
        self.api.remove("1", "einstein")

    def test_update(self):
        self.api.update("", "1", "einstein")

    def test_list_received(self):
        self.api.list_received("/", "einstein")

    def test_update_received(self):
        self.api.update_received("", "1", "marie")
