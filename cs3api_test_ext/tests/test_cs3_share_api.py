from unittest import TestCase

import http
import time

import grpc
import cs3.gateway.v1beta1.gateway_api_pb2 as gateway
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway
import cs3.sharing.collaboration.v1beta1.collaboration_api_pb2 as sharing
import cs3.sharing.collaboration.v1beta1.resources_pb2 as sharing_res
import cs3.sharing.collaboration.v1beta1.collaboration_api_pb2_grpc as sharing_grpc
import cs3.sharing.collaboration.v1beta1.resources_pb2 as sh
# import cs3.sharing.ocm.v1beta1 as sh
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
        self.fail()

    def test_remove(self):
        self.fail()

    def test_update(self):
        self.fail()

    def test_list_received(self):
        self.fail()

    def test_update_received(self):
        self.fail()
