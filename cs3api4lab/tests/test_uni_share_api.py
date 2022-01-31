from cs3api4lab.tests.share_test_base import ShareTestBase
import random
import string

from unittest import TestCase
from traitlets.config import LoggingConfigurable
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi
from cs3api4lab.api.share_api_facade import ShareAPIFacade

from cs3api4lab.tests.extensions import *

class TestCs3UniShareApi(ShareTestBase, TestCase, LoggingConfigurable):
    einstein_id = '4c510ada-c86b-4815-8820-42cdf82c3d51'
    einstein_idp = 'cernbox.cern.ch'
    marie_id = 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c'
    marie_idp = 'cesnet.cz'
    richard_id = '932b4540-8d16-481e-8ef4-588e4b6b151c'
    richard_idp = 'example.org'
    receiver_role = 'editor'
    receiver_grantee_type = 'user'
    file_path = '/home/test.txt'
    storage_id = '123e4567-e89b-12d3-a456-426655440000'
    share_id = None
    ocm_share_id = None
    ocm_file_name = None
    file_name = None

    def test_create(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.ocm_file_name = self.file_path + self.get_random_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']
            share_list = self.uni_api.list_shares()
            contains = False
            contains_ocm = False
            for share in share_list['content']:
                if share['path'].__contains__(self.file_name.split('/')[-1]):
                    contains = True
                if share['path'].__contains__(self.ocm_file_name.split('/')[-1]):
                    contains_ocm = True
            if not (contains and contains_ocm):
                raise Exception("Shares not present")
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_list_received(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.ocm_file_name = self.file_path + self.get_random_suffix()
            created_ocm_share = self.create_ocm_share('marie', self.einstein_id, self.einstein_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']
            share_list = self.uni_api.list_received()
            contains = False
            contains_ocm = False
            for share in share_list['content']:
                if share['path'].__contains__(self.file_name.split('/')[-1]):
                    contains = True
                if share['path'].__contains__(self.ocm_file_name.split('/')[-1]):
                    contains_ocm = True
            if not (contains and contains_ocm):
                raise Exception("Shares not present")
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('marie', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('marie', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_update_received_share(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            self.uni_api.update_received(self.share_id, 'ACCEPTED')
            received_file_path = '/home/MyShares/' + self.file_name.split('/')[-1]
            file_stat = self.file_api.stat(received_file_path, self.storage_id)

            self.assertEqual(file_stat['filepath'], received_file_path, 'Share not updated')
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_update_received_ocm_share(self):
        try:
            self.ocm_file_name = self.file_path + self.get_random_suffix()

            created_ocm_share = self.create_ocm_share('marie', self.einstein_id, self.einstein_idp, self.ocm_file_name)
            self.ocm_share_id = created_ocm_share['id']

            received_ocm_share = [share for share in self.ocm_api.list_received().shares if share.share.resource_id.opaque_id == self.ocm_file_name]
            self.assertTrue(received_ocm_share, 'OCM Received share not found')

            self.uni_api.update_received(received_ocm_share[0].share.id.opaque_id, 'ACCEPTED')

            #todo fix: accepted files from ocm are not son in /home/My/shares
            
            # received_ocm_file_path = '/home/MyShares/' + self.ocm_file_name.split('/')[-1]
            # ocm_file_stat = self.file_api.stat(received_ocm_file_path, self.storage_id)
            # self.assertEqual(ocm_file_stat['filepath'], received_ocm_file_path, 'Share not updated')
        finally:
            if self.ocm_share_id:
                self.remove_test_ocm_share('marie', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('marie', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_remove(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.ocm_file_name = self.file_path + self.get_random_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']

            share_list = self.uni_api.list_shares()
            contains = False
            contains_ocm = False
            for share in share_list['content']:
                if share['path'].__contains__(self.file_name.split('/')[-1]):
                    contains = True
                if share['path'].__contains__(self.ocm_file_name.split('/')[-1]):
                    contains_ocm = True
            if not (contains and contains_ocm):
                raise Exception("Shares not present")

            self.uni_api.remove(self.share_id)
            self.uni_api.remove(self.ocm_share_id)

            share_list = self.uni_api.list_shares()
            contains = False
            contains_ocm = False
            for share in share_list['content']:
                if share['path'].__contains__(self.file_name.split('/')[-1]):
                    contains = True
                if share['path'].__contains__(self.ocm_file_name.split('/')[-1]):
                    contains_ocm = True
            if contains or contains_ocm:
                raise Exception("Shares not removed")
        finally:
            if contains:
                self.remove_test_share('einstein', self.share_id)
            if contains_ocm:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_get_grantees_for_file(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.ocm_file_name = self.file_path + self.get_random_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.share_id = created_share['opaque_id']
            self.ocm_share_id = created_ocm_share['id']

            grantees = self.uni_api.list_grantees_for_file(self.file_name)
            if not grantees['shares']:
                raise Exception("Grantees not found")

            grantees = self.uni_api.list_grantees_for_file(self.ocm_file_name)
            if not grantees['shares']:
                raise Exception("Grantees not found")

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)
