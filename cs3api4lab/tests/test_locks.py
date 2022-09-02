import json

from unittest import TestCase
from time import sleep
from cs3api4lab.tests.share_test_base import ShareTestBase
import urllib.parse

class TestLocks(ShareTestBase, TestCase):
    einstein_id = '4c510ada-c86b-4815-8820-42cdf82c3d51'
    einstein_idp = 'cernbox.cern.ch'
    marie_id = 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c'
    marie_idp = 'cesnet.cz'
    richard_id = '932b4540-8d16-481e-8ef4-588e4b6b151c'
    richard_idp = 'example.org'
    file_path = '/home/test_locks.txt'
    shared_file_path = '/reva/einstein/test_locks.txt'
    share_id = None
    conflict_name = None
    
    def test_lock_created_when_file_written(self):
        self.file_name = self.file_path + self.get_random_suffix()

        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            self.file_api.write_file(self.file_name, 'content')

            file_ref = self.storage_logic.get_unified_file_ref(self.file_name, '/')
            file_info = self.storage_logic._stat_internal(file_ref).info

            self.assertTrue(file_info.arbitrary_metadata.metadata)
            self.assertIn("lock_einstein_cernbox.cern.ch_4c510ada-c86b-4815-8820-42cdf82c3d51", file_info.arbitrary_metadata.metadata)
            
            lock = json.loads(urllib.parse.unquote(file_info.arbitrary_metadata.metadata["lock_einstein_cernbox.cern.ch_4c510ada-c86b-4815-8820-42cdf82c3d51"]))
            self.assertEqual(lock['username'], 'einstein')
            self.assertEqual(lock['idp'], 'cernbox.cern.ch')
            self.assertEqual(lock['opaque_id'], '4c510ada-c86b-4815-8820-42cdf82c3d51')

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_lock_created_when_file_read(self):
        self.file_name = self.file_path + self.get_random_suffix()

        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            for chunk in self.file_api.read_file(self.file_name):
                continue

            file_ref = self.storage_logic.get_unified_file_ref(self.file_name, '/')
            file_info = self.storage_logic._stat_internal(file_ref).info

            self.assertTrue(file_info.arbitrary_metadata.metadata)
            self.assertIn("lock_einstein_cernbox.cern.ch_4c510ada-c86b-4815-8820-42cdf82c3d51", file_info.arbitrary_metadata.metadata)
            
            lock = json.loads(urllib.parse.unquote(file_info.arbitrary_metadata.metadata["lock_einstein_cernbox.cern.ch_4c510ada-c86b-4815-8820-42cdf82c3d51"]))
            self.assertEqual(lock['username'], 'einstein')
            self.assertEqual(lock['idp'], 'cernbox.cern.ch')
            self.assertEqual(lock['opaque_id'], '4c510ada-c86b-4815-8820-42cdf82c3d51')

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_write_file_locked_conflict_created(self):
        suffix = self.get_random_suffix()
        self.file_name = self.file_path + suffix
        shared_name = self.shared_file_path + suffix

        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            self.file_api.write_file(self.file_name, 'content')
            self.conflict_name = self.richard_file_api.write_file(shared_name, "richard_content")
            
            lock_stat = self.richard_file_api.stat(self.conflict_name)
            self.assertEqual(lock_stat['filepath'], self.conflict_name)

            content = self.read_file_content(self.richard_file_api, self.conflict_name)
            self.assertEqual(content, 'richard_content', 'File ' + self.file_name + ' should contain the string: ' + 'richard_content')
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)
            if self.conflict_name:
                self.remove_test_file('richard', self.conflict_name)

    def test_write_dir_file_locked(self):
        suffix = self.get_random_suffix()
        self.file_name = '/home/testdir/test_locks.txt' + suffix
        shared_name = '/reva/einstein/testdir/test_locks.txt' + suffix

        try:
            try:
                self.file_api.create_directory('/home/testdir')
            except:
                pass #ignore already existing directory
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            self.file_api.write_file(self.file_name, 'content')
            self.conflict_name = self.richard_file_api.write_file(shared_name, "richard_content")
            
            lock_stat = self.richard_file_api.stat(self.conflict_name)
            self.assertEqual(lock_stat['filepath'], self.conflict_name)

            content = self.read_file_content(self.richard_file_api, self.conflict_name)
            self.assertEqual(content, 'richard_content', 'File ' + self.file_name + ' should contain the string: ' + 'richard_content')
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)
            if self.conflict_name:
                self.remove_test_file('richard', self.conflict_name)

    def test_write_file_lock_expired(self):
        suffix = self.get_random_suffix()
        self.file_name = self.file_path + suffix
        shared_name = self.shared_file_path + suffix

        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            self.file_api.write_file(self.file_name, 'content')

            sleep(12)
            self.richard_file_api.write_file(shared_name, "richard_content")

            content = self.read_file_content(self.richard_file_api, shared_name)
            self.assertEqual(content, 'richard_content', 'File ' + self.file_name + ' should contain the string: ' + 'richard_content')
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_write_by_lock_owner_file_locked(self):
        self.file_name = self.file_path + self.get_random_suffix()

        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            self.file_api.write_file(self.file_name, 'content')

            self.file_api.write_file(self.file_name, 'new_content')

            content = self.read_file_content(self.file_api, self.file_name)
            self.assertEqual(content, 'new_content', 'File ' + self.file_name + ' should contain the string: ' + 'new_content')

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)
