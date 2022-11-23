from cs3api4lab.tests.share_test_base import ShareTestBase

from unittest import TestCase

from unittest import skip


class TestCs3UniShareApi(ShareTestBase, TestCase):
    einstein_id = '4c510ada-c86b-4815-8820-42cdf82c3d51'
    einstein_idp = 'cernbox.cern.ch'
    marie_id = 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c'
    marie_idp = 'cesnet.cz'
    richard_id = '932b4540-8d16-481e-8ef4-588e4b6b151c'
    richard_idp = 'example.org'
    file_path = '/home/test.txt'
    share_id = None
    ocm_share_id = None
    ocm_file_name = None
    file_name = None

    def test_create(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            share_list = self.uni_api.list_shares()
            contains = False
            for share in share_list['content']:
                if self.file_name.split('/')[-1] in share['path']:
                    contains = True
            self.assertTrue(contains, "Share not present")
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    @skip
    def test_create_ocm(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            self.ocm_file_name = self.file_path + self.get_random_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.ocm_share_id = created_ocm_share['id']
            share_list = self.uni_api.list_shares()
            contains_ocm = False
            for share in share_list['content']:
                if self.ocm_file_name.split('/')[-1] in share['path']:
                    contains_ocm = True
            self.assertTrue(contains_ocm, "OCM Share not present")
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_list_with_filter(self):
        if not self.config.enable_ocm:
            self.skipTest('OCM disabled')
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.file_name)
            self.ocm_share_id = created_ocm_share['id']

            share_list = self.uni_api.list_shares(filter_duplicates=True)
            file_shares = list(filter(lambda s: s['name'] == self.file_name.split('/')[-1], share_list['content']))
            self.assertEqual(len(file_shares), 1)

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_list_without_filter(self):
        if not self.config.enable_ocm:
            self.skipTest('OCM disabled')
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.file_name)
            self.ocm_share_id = created_ocm_share['id']

            share_list = self.uni_api.list_shares(filter_duplicates=False)
            file_shares = list(filter(lambda s: s['name'] == self.file_name.split('/')[-1], share_list['content']))
            self.assertEqual(len(file_shares), 2)

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_list_received(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            share_list = self.uni_api.list_received()
            contains = False
            for share in share_list['content']:
                if self.file_name.split('/')[-1] in share['path']:
                    contains = True
            self.assertTrue(contains, "Share not present")
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_list_received_not_accepted(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            share_list = self.uni_api.list_received('ACCEPTED')
            list_of_shared_files = []
            shared_file = self.file_name.split('/')[-1]

            for share in share_list['content']:
                list_of_shared_files.append(share['name'])

            self.assertNotIn(shared_file, list_of_shared_files, "Share not present")

        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    @skip
    def test_list_received_ocm(self):
        try:
            self.ocm_file_name = self.file_path + self.get_random_suffix()
            created_ocm_share = self.create_ocm_share('marie', self.einstein_id, self.einstein_idp, self.ocm_file_name)
            self.ocm_share_id = created_ocm_share['id']
            share_list = self.uni_api.list_received()
            contains_ocm = False
            for share in share_list['content']:
                if self.ocm_file_name.split('/')[-1] in share['path']:
                    contains_ocm = True
            self.assertTrue(contains_ocm, "OCM Share not present")
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
            file_stat = self.file_api.stat_info(received_file_path, self.storage_id)

            self.assertEqual(file_stat['filepath'], received_file_path, 'Share not updated')
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    @skip
    def test_update_received_ocm_share(self):
        try:
            self.ocm_file_name = self.file_path + self.get_random_suffix()

            created_ocm_share = self.create_ocm_share('marie', self.einstein_id, self.einstein_idp, self.ocm_file_name)
            self.ocm_share_id = created_ocm_share['id']

            received_ocm_share = [share for share in self.ocm_api.list_received().shares if share.share.resource_id.opaque_id == self.ocm_file_name]
            self.assertTrue(received_ocm_share, 'OCM Received share not found')

            self.uni_api.update_received(received_ocm_share[0].share.id.opaque_id, 'ACCEPTED')

            #todo fix: accepted files from ocm are not present in /home/My/shares
            
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
            self.share_id = created_share['opaque_id']

            share_list = self.uni_api.list_shares()
            contains = False
            for share in share_list['content']:
                if self.file_name.split('/')[-1] in share['path']:
                    contains = True
            self.assertTrue(contains, "Shares not present")

            self.uni_api.remove(self.share_id)

            share_list = self.uni_api.list_shares()
            contains = False
            for share in share_list['content']:
                if self.file_name.split('/')[-1] in share['path']:
                    contains = True
            self.assertFalse(contains, "Shares not removed")
        finally:
            if contains:
                self.remove_test_share('einstein', self.share_id)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    @skip
    def test_remove_ocm(self):
        try:
            self.ocm_file_name = self.file_path + self.get_random_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.ocm_share_id = created_ocm_share['id']

            share_list = self.uni_api.list_shares()
            contains_ocm = False
            for share in share_list['content']:
                if self.ocm_file_name.split('/')[-1] in share['path']:
                    contains_ocm = True
            self.assertTrue(contains_ocm, "OCM Share not present")

            self.uni_api.remove(self.ocm_share_id)

            share_list = self.uni_api.list_shares()
            contains_ocm = False
            for share in share_list['content']:
                if self.ocm_file_name.split('/')[-1] in share['path']:
                    contains_ocm = True
            self.assertTrue(contains_ocm, "OCM Share not removed")

        finally:
            if contains_ocm:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_get_grantees_for_file(self):
        try:
            expected_grantee_opaque = '932b4540-8d16-481e-8ef4-588e4b6b151c'
            expected_grantee_idp = 'example.org'
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            grantees = self.uni_api.list_grantees_for_file(self.file_name)

            self.assertTrue(
                list(share for share in grantees['shares']
                     if share['grantee']['opaque_id'] == expected_grantee_opaque
                     and share['grantee']['idp'] == expected_grantee_idp),
                "Grantee not present")

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_get_grantees_for_file_with_drive_name(self):
        try:
            expected_grantee_opaque = '932b4540-8d16-481e-8ef4-588e4b6b151c'
            expected_grantee_idp = 'example.org'
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            file_path = "cs3drive:" + self.file_name[1:]
            grantees = self.uni_api.list_grantees_for_file(file_path)

            self.assertTrue(
                list(share for share in grantees['shares']
                     if share['grantee']['opaque_id'] == expected_grantee_opaque
                     and share['grantee']['idp'] == expected_grantee_idp),
                "Grantee not present")

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)
    
    def test_get_grantees_for_file_with_drive_name_starting_with_slash(self):
        try:
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            file_path = "/cs3drive:" + self.file_name[1:]
            grantees = self.uni_api.list_grantees_for_file(file_path)
            self.assertTrue(grantees['shares'], "Grantees not found")

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_get_grantees_for_file_with_drive_name_starting_with_slash(self):
        try:
            expected_grantee_opaque = '932b4540-8d16-481e-8ef4-588e4b6b151c'
            expected_grantee_idp = 'example.org'
            self.file_name = self.file_path + self.get_random_suffix()
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            file_path = "/cs3drive:" + self.file_name[1:]
            grantees = self.uni_api.list_grantees_for_file(file_path)

            self.assertTrue(
                list(share for share in grantees['shares']
                     if share['grantee']['opaque_id'] == expected_grantee_opaque
                     and share['grantee']['idp'] == expected_grantee_idp),
                "Grantee not present")

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    @skip
    def test_get_grantees_for_file_ocm(self):
        try:
            self.ocm_file_name = self.file_path + self.get_random_suffix()
            created_ocm_share = self.create_ocm_share('einstein', self.marie_id, self.marie_idp, self.ocm_file_name)
            self.ocm_share_id = created_ocm_share['id']

            grantees = self.uni_api.list_grantees_for_file(self.ocm_file_name)
            self.assertTrue(grantees['shares'], "Grantees not found")

        finally:
            if self.ocm_share_id:
                self.remove_test_ocm_share('einstein', self.ocm_share_id)
            if self.ocm_file_name:
                self.remove_test_file('einstein', self.ocm_file_name)
