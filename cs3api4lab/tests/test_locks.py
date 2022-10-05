import json

from unittest import TestCase
from time import sleep

from google.protobuf.json_format import MessageToDict

from cs3api4lab.tests.share_test_base import ShareTestBase
from cs3api4lab.exception.exceptions import FileLockedError
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
            self.file_api.write_file(self.file_name, 'content')  # this only creates file, it's not locked
            self.file_api.write_file(self.file_name, 'content')  # this writes to existing file and locks it

            file_info = self.file_api.stat_info(self.file_name)
            opaque_id = urllib.parse.unquote(file_info['inode']['opaque_id'])
            storage_id = urllib.parse.unquote(file_info['inode']['storage_id'])

            file_info2 = self.file_api.stat_info(opaque_id, storage_id)
            lock = json.loads(urllib.parse.unquote(file_info2['arbitrary_metadata']['metadata']['cs3apis4lab_lock']))
            self.assertTrue(file_info2['arbitrary_metadata']['metadata']['cs3apis4lab_lock'])
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

            stat = self.file_api.stat_info(self.file_name)
            for _ in self.file_api.read_file(stat):
                continue

            file_ref = self.storage_api.get_unified_file_ref(self.file_name, '/')
            file_info = self.storage_api._stat_internal(file_ref).info
            arbitrary_metadata = MessageToDict(file_info.arbitrary_metadata)
            lock = json.loads(urllib.parse.unquote(arbitrary_metadata['metadata']['cs3apis4lab_lock']))
            self.assertEqual(lock['username'], 'einstein')
            self.assertEqual(lock['idp'], 'cernbox.cern.ch')
            self.assertEqual(lock['opaque_id'], '4c510ada-c86b-4815-8820-42cdf82c3d51')

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_read_locked_file_by_grantee(self):
        suffix = self.get_random_suffix()
        self.file_name = self.file_path + suffix
        shared_file_path = self.shared_file_path + suffix
        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            stat = self.file_api.stat_info(shared_file_path)
            content = ''
            for chunk in self.richard_file_api.read_file(stat):
                content += chunk.decode('utf-8')
            self.assertEqual(content, self.content)
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_write_new_locked_file_by_grantee(self):
        suffix = self.get_random_suffix()
        self.file_name = self.file_path + suffix
        shared_file_path = self.shared_file_path + suffix
        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            self.richard_file_api.write_file(shared_file_path, 'content')
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_write_locked_file_lock_expired_by_grantee(self):
        suffix = self.get_random_suffix()
        self.file_name = self.file_path + suffix
        shared_file_path = self.shared_file_path + suffix
        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            sleep(12)
            self.richard_file_api.write_file(shared_file_path, 'content')
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_read_file_locked_by_grantee(self):
        suffix = self.get_random_suffix()
        self.file_name = self.file_path + suffix
        shared_file_path = self.shared_file_path + suffix
        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            sleep(12)
            self.richard_file_api.write_file(shared_file_path, 'content')
            stat = self.file_api.stat_info(shared_file_path)
            content = ''
            for chunk in self.file_api.read_file(stat):
                content += chunk.decode('utf-8')
            self.assertEqual(content, 'content')
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_write_file_locked_by_grantee(self):
        suffix = self.get_random_suffix()
        self.file_name = self.file_path + suffix
        shared_file_path = self.shared_file_path + suffix
        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            sleep(12)
            self.richard_file_api.write_file(shared_file_path, 'content')
            with self.assertRaises(FileLockedError):
                self.file_api.write_file(shared_file_path, 'content')
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)

    def test_write_file_lock_expired(self):
        suffix = self.get_random_suffix()
        self.file_name = self.file_path + suffix
        shared_name = self.shared_file_path + suffix

        try:
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            self.file_api.write_file(self.file_name, 'content')

            stat = self.file_api.stat_info(self.file_name)
            for _ in self.file_api.read_file(stat):  #read file to lock it
                continue

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

            stat = self.file_api.stat_info(self.file_name)
            for _ in self.file_api.read_file(stat):  # read file to lock it
                continue

            self.file_api.write_file(self.file_name, 'new_content')

            content = self.read_file_content(self.file_api, self.file_name)
            self.assertEqual(content, 'new_content', 'File ' + self.file_name + ' should contain the string: ' + 'new_content')

        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            self.remove_test_file('einstein', self.file_name)
