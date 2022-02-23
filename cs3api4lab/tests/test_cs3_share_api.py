import posixpath

from cs3api4lab.tests.share_test_base import ShareTestBase
from unittest import TestCase

from cs3api4lab.exception.exceptions import ShareNotFoundError, ShareError, ResourceNotFoundError


class TestCs3ShareApi(ShareTestBase, TestCase):
    einstein_id = '4c510ada-c86b-4815-8820-42cdf82c3d51'
    einstein_idp = 'cernbox.cern.ch'
    richard_id = '932b4540-8d16-481e-8ef4-588e4b6b151c'
    richard_idp = 'example.org'
    file_path = '/home/test.txt'
    share_id = None
    ocm_share_id = None
    ocm_file_name = None
    file_name = None

    #todo this is a template test. Refactor all other tests using this as an example
    def test_create_share(self):
        '''creates a file and shares it with another user'''

        #given
        user = self.config.client_id
        share_id = None
        file_name = posixpath.join(self.config.mount_dir, "test_create_share.txt")
        self.remove_share_and_file_by_path(user, file_name)
        try:
            self.create_test_file(user, file_name)

            #when
            created_share = self.create_share(user, self.richard_id, self.richard_idp, file_name)

            #then
            self.assertTrue(created_share, 'Error when creating share')
            share_id = created_share['opaque_id']
            share_list = self.share_api.list()
            self.assertTrue(list(share for share in share_list.shares if share.id.opaque_id == created_share['opaque_id']),
                            "Share not present")
        finally:
            self.clean_up_share(user, share_id)
            self.clean_up_file(user, file_name)

    def test_create(self):
        try:
            self.file_name = self.file_path + "_test_create"
            self.create_test_file('einstein', self.file_name)
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            share_list = self.share_api.list()
            self.assertTrue(list(share for share in share_list.shares if share.id.opaque_id == created_share['opaque_id']),
                            "Share not present")
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_create_share_already_exists(self):
        try:
            self.file_name = self.file_path + "_test_create_share_already_exists"
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            self.share_api.update_received(self.share_id, 'ACCEPTED')

            with self.assertRaises(ShareError):
                self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            # todo change this after https://github.com/cs3org/reva/issues/2847 is fixed
            # with self.assertRaises(ShareAlreadyExistsError) as context:
            #     self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            # self.assertIn("Share already exists for file:", context.exception.args[0])
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_create_share_file_doesnt_exist(self):
        self.file_name = self.file_path + "_test_create_share_file_doesnt_exist"

        with self.assertRaises(ResourceNotFoundError) as context:
            self.richard_share_api.create(self.storage_id, self.file_name, self.einstein_id, self.einstein_idp,
                                          self.receiver_role, self.receiver_grantee_type)
        self.assertIn("Resource not found", context.exception.args[0])

    def test_get_share(self):
        """
        This tests if get share works properly
        1. Create share
        2. Get Share with correct ID
        3. Assert if created share opaque_id is equal to response opaque_id
        """

        try:
            self.file_name = self.file_path + "_test_get_share"
            self.create_test_file('einstein', self.file_name)
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            share = self.share_api.get(self.share_id)
            self.assertEqual(self.share_id, share.share.id.opaque_id, "Created share and response share opaque_id are "
                                                                      "not equal")
        finally:
            if self.share_id:
                self.remove_test_share('einstein', self.share_id)
            if self.file_name:
                self.remove_test_file('einstein', self.file_name)

    def test_get_share_incorrect_id(self):
        """
        This tests checks if share_api.get() single share raises an exception when incorrect id is given
        """
        incorrect_id = "1"
        with self.assertRaises(ShareNotFoundError) as context:
            self.share_api.get(incorrect_id)

        self.assertIn(f"Error getting share for opaque_id {incorrect_id}", context.exception.args[0])

    def test_remove_share_doesnt_exist(self):
        """This test if share_api.remove raises an error when share doesn't exist"""

        incorrect_id = "1"
        with self.assertRaises(Exception) as context:
            self.share_api.remove(incorrect_id)

        self.assertIn('Incorrect server response:', context.exception.args[0])

    def test_remove(self):
        """
        This tests if existing share is correctly removed:
            1. Create share
            2. Call remove share
            3. Check if share_api.get() raises an exception (share does not exist)
        """

        try:
            self.file_name = self.file_path + "_test_remove"
            self.create_test_file('einstein', self.file_name)
            created_share = self.create_share('einstein', self.richard_id, self.richard_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            self.share_api.remove(self.share_id)

            with self.assertRaises(ShareNotFoundError) as context:
                self.share_api.get(self.share_id)

            self.assertIn("Error getting share for opaque_id", context.exception.args[0])

        finally:
            self.remove_test_file('einstein', self.file_name)

    def test_list_received(self):
        try:
            self.file_name = self.file_path + "_test_list_received"
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.share_id = created_share['opaque_id']
            share_list = self.share_api.list_received()
            self.assertTrue(list(share for share in share_list.shares if share.share.id.opaque_id == created_share['opaque_id']),
                            "Share not present")
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_update_received_share(self):
        try:
            self.file_name = self.file_path + "_test_update_received_share"
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            self.share_api.update_received(self.share_id, 'ACCEPTED')
            received_file_path = '/home/MyShares/' + self.file_name.split('/')[-1]
            file_stat = self.file_api.stat_info(received_file_path, self.storage_id)

            self.assertEqual(file_stat['filepath'], received_file_path, 'Share not updated')
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_read_share(self):
        try:
            self.file_name = self.file_path + "_test_read_share"
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            self.share_api.update_received(self.share_id, 'ACCEPTED')
            received_file_path = '/home/MyShares/' + self.file_name.split('/')[-1]
            file_stat = self.file_api.stat_info(received_file_path, self.storage_id)
            self.assertEqual(file_stat['filepath'], received_file_path, 'Share not updated')

            self.clear_locks_on_file(received_file_path)
            content = ''
            for chunk in self.file_api.read_file(received_file_path, self.config.endpoint):
                content += chunk.decode('utf-8')
            self.assertEqual(content, self.content)
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_write_share(self):
        try:
            self.file_name = self.file_path + "test_write_share"
            created_share = self.create_share('richard', self.einstein_id, self.einstein_idp, self.file_name)
            self.share_id = created_share['opaque_id']

            self.share_api.update_received(self.share_id, 'ACCEPTED')
            received_file_path = '/home/MyShares/' + self.file_name.split('/')[-1]
            file_stat = self.file_api.stat_info(received_file_path, self.storage_id)
            self.assertEqual(file_stat['filepath'], received_file_path, 'Share not updated')

            self.clear_locks_on_file(received_file_path)
            self.file_api.write_file(received_file_path, self.content + self.content)
            content = ''
            for chunk in self.file_api.read_file(received_file_path, self.config.endpoint):
                content += chunk.decode('utf-8')
            self.assertEqual(content, self.content + self.content)
        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.file_name:
                self.remove_test_file('richard', self.file_name)

    def test_read_write_file_in_shared_container(self):
        try:
            self.container_name = '/home/test_container' + "test_read_write_file_in_shared_container"
            created_share = self.create_container_share('richard', self.einstein_id, self.einstein_idp, self.container_name)
            self.share_id = created_share['opaque_id']
            file_name = '/test.txt' + self.get_random_suffix()
            self.create_test_file('richard', self.container_name + file_name)

            self.share_api.update_received(self.share_id, 'ACCEPTED')
            received_container_path = '/home/MyShares/' + self.container_name.split('/')[-1]
            dir_read = self.file_api.read_directory(received_container_path)
            self.assertEqual('/' + dir_read[0].path.split('/')[-1], file_name)

            self.clear_locks_on_file(received_container_path + file_name)
            content = ''
            for chunk in self.file_api.read_file(received_container_path + file_name, self.config.endpoint):
                content += chunk.decode('utf-8')
            self.assertEqual(content, self.content)

            self.file_api.write_file(received_container_path + file_name, self.content + self.content)
            self.clear_locks_on_file(received_container_path + file_name)
            content = ''
            for chunk in self.richard_file_api.read_file(self.container_name + file_name, self.config.endpoint):
                content += chunk.decode('utf-8')
            self.assertEqual(content, self.content + self.content)

        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.container_name:
                self.remove_test_file('richard', self.container_name)

    def test_create_file_and_dir_in_shared_container(self):
        try:
            self.container_name = '/home/test_container' + "_test_create_file_and_dir_in_shared_container"
            created_share = self.create_container_share('richard', self.einstein_id, self.einstein_idp, self.container_name)
            self.share_id = created_share['opaque_id']
            self.share_api.update_received(self.share_id, 'ACCEPTED')

            inner_container = '/test_container' + "_test_create_file_and_dir_in_shared_container_inner_container"
            file_name = '/test.txt' + "_test_create_file_and_dir_in_shared_container_file_naem"

            received_container_path = '/home/MyShares/' + self.container_name.split('/')[-1]
            self.create_test_container('einstein', received_container_path + inner_container)
            self.create_test_file('einstein', received_container_path + inner_container + file_name)

            self.clear_locks_on_file(received_container_path + inner_container + file_name)
            content = ''
            for chunk in self.richard_file_api.read_file(self.container_name + inner_container + file_name, self.config.endpoint):
                content += chunk.decode('utf-8')
            self.assertEqual(content, self.content)

        finally:
            if self.share_id:
                self.remove_test_share('richard', self.share_id)
            if self.container_name:
                self.remove_test_file('richard', self.container_name)
