import unittest
from unittest import TestCase
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from traitlets.config import LoggingConfigurable


class TestCs3FileApi(TestCase):
    client_id = None
    endpoint = None

    def setUp(self):
        self.log = LoggingConfigurable().log
        config = Cs3ConfigManager.get_config()
        self.client_id = config.client_id
        self.endpoint = config.endpoint
        self.storage = Cs3FileApi(self.log)

    def test_stat(self):
        file_id = "/test.txt"
        message = "Lorem ipsum dolor sit amet..."
        try:
            self.storage.write_file(file_id, message, self.endpoint)
            stat_info = self.storage.stat_info(file_id, self.endpoint)
            self.assertIsInstance(stat_info, dict)
            self.assertTrue('mtime' in stat_info, 'Missing mtime from stat output')
            self.assertTrue('size' in stat_info, 'Missing size from stat output')
        finally:
            self.storage.remove(file_id, self.endpoint)

    def test_stat_no_file(self):
        with self.assertRaises(IOError, msg='No such file or directory'):
            self.storage.stat_info('/hopefullynotexisting', self.endpoint)

    def test_read_file(self):

        content_to_write = b'bla\n'
        content_check = 'bla\n'
        file_path = "/test_read.txt"
        try:
            self.storage.write_file(file_path, content_to_write, self.endpoint)
            content = ''
            for chunk in self.storage.read_file(file_path, self.endpoint):
                self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
                content += chunk.decode('utf-8')
            self.assertEqual(content, content_check,
                             'File ' + file_path + ' should contain the string: ' + content_check)
        finally:
            self.storage.remove(file_path, self.endpoint)

    def test_read_file_by_id(self):
        content_to_write = b'bla_by_id\n'
        content_to_check = 'bla_by_id\n'
        file_path = "/test_read_by_id.txt"
        try:
            self.storage.write_file(file_path, content_to_write, self.endpoint)
            stat = self.storage.stat_info(file_path)
            content = ''
            for chunk in self.storage.read_file(file_path, self.endpoint):
                self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
                content += chunk.decode('utf-8')

            self.assertEqual(stat['inode']['opaque_id'], 'fileid-einstein%2Ftest_read_by_id.txt')
            self.assertEqual(stat['inode']['storage_id'], '123e4567-e89b-12d3-a456-426655440000')
            self.assertEqual(content, content_to_check,
                             'File ' + file_path + ' should contain the string: ' + content_to_check)
        finally:
            self.storage.remove(file_path, self.endpoint)

    def test_read_file_by_share_path(self):
        content_to_write = b'bla_by_share\n'
        content_to_check = 'bla_by_share\n'
        file_path = "/test_read_by_share_path.txt"
        try:
            self.storage.write_file(file_path, content_to_write, self.endpoint)
            stat = self.storage.stat_info(file_path)
            stat_by_id = self.storage.stat_info(stat['inode']['opaque_id'], stat['inode']['storage_id'])
            content = ''
            for chunk in self.storage.read_file(file_path, self.endpoint):
                self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
                content += chunk.decode('utf-8')
            self.assertEqual(stat_by_id['filepath'], '/reva/einstein/test_read_by_share_path.txt')
            self.assertEqual(content, content_to_check,
                             'File ' + file_path + ' should contain the string: ' + content_to_check)
        finally:
            self.storage.remove(file_path, self.endpoint)

    def test_read_file_no_file(self):
        file_path = "/test_read_no_existing_file.txt"
        content = ''
        with self.assertRaises(IOError, msg='No such file or directory'):
            for chunk in self.storage.read_file(file_path, self.endpoint):
                content += chunk.decode('utf-8')

    def test_write_file(self):
        buffer = b"Testu form cs3 Api"
        file_id = "/testfile.txt"
        try:
            self.storage.write_file(file_id, buffer, self.endpoint)
            stat_info = self.storage.stat_info(file_id, self.endpoint)
            self.assertIsInstance(stat_info, dict)
        finally:
            self.storage.remove(file_id, self.endpoint)

    def test_write_empty_file(self):
        buffer = b""
        file_id = "/zero_test_file.txt"
        try:
            self.storage.write_file(file_id, buffer, self.endpoint)
            stat_info = self.storage.stat_info(file_id, self.endpoint)
            self.assertIsInstance(stat_info, dict)
        finally:
            self.storage.remove(file_id, self.endpoint)

    def test_remove_file(self):
        file_id = "/file_to_remove.txt"
        buffer = b"ebe5tresbsrdthbrdhvdtr"
        try:
            self.storage.write_file(file_id, buffer, self.endpoint)
            self.storage.remove(file_id, self.endpoint)
            with self.assertRaises(IOError):
                self.storage.stat_info(file_id, self.endpoint)
        except:
            self.storage.remove(file_id, self.endpoint)

    def test_read_directory(self):
        file_id = "/"
        read_directory = self.storage.read_directory(file_id, self.endpoint)
        self.assertIsNotNone(read_directory[0])
        self.assertIsNotNone(read_directory[0].path)

    def test_move_file(self):
        src_id = "/file_to_rename.txt"
        buffer = b"ebe5tresbsrdthbrdhvdtr"
        dest_id = "/file_after_rename.txt"
        try:
            self.storage.remove(dest_id)
        except:
            pass
        try:
            self.storage.write_file(src_id, buffer, self.endpoint)
            self.storage.move(src_id, dest_id, self.endpoint)
            self.storage.remove(dest_id, self.endpoint)
            with self.assertRaises(IOError):
                self.storage.stat_info(dest_id, self.endpoint)
        finally:
            try:
                self.storage.remove(src_id, self.endpoint)
            except: pass
            try:
                self.storage.remove(dest_id, self.endpoint)
            except: pass

    def test_move_file_already_exists(self):
        try:
            source_path = "/file_to_rename.txt"
            buffer = b"ebe5tresbsrdthbrdhvdtr"
            destination_path = "/file_after_rename.txt"
            self.storage.write_file(source_path, buffer, self.endpoint)
            self.storage.write_file(destination_path, buffer, self.endpoint)

            with self.assertRaises(IOError) as context:
                self.storage.move(source_path, destination_path, self.endpoint)
            self.assertEqual("file already exists", context.exception.args[0])
        finally:
            try:
                self.storage.remove(source_path, self.endpoint)
            except: pass
            try:
                self.storage.remove(destination_path, self.endpoint)
            except: pass

if __name__ == '__main__':
    unittest.main()
