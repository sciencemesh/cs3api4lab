import unittest
from unittest import TestCase
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from traitlets.config import LoggingConfigurable


class TestCs3FileApi(TestCase, LoggingConfigurable):
    client_id = None
    endpoint = None

    def setUp(self):
        config = Cs3ConfigManager.get_config()
        self.client_id = config['client_id']
        self.endpoint = config['endpoint']
        self.storage = Cs3FileApi(self.log)

    def test_stat(self):
        file_id = "/test.txt"
        message = "Lorem ipsum dolor sit amet..."

        self.storage.write_file(file_id, self.client_id, message, self.endpoint)

        stat_info = self.storage.stat(file_id, self.client_id, self.endpoint)

        self.assertIsInstance(stat_info, dict)
        self.assertTrue('mtime' in stat_info, 'Missing mtime from stat output')
        self.assertTrue('size' in stat_info, 'Missing size from stat output')

        self.storage.remove(file_id, self.client_id, self.endpoint)

    def test_stat_no_file(self):
        with self.assertRaises(IOError, msg='No such file or directory'):
            self.storage.stat('/hopefullynotexisting', self.client_id, self.endpoint)

    def test_read_file(self):

        content_to_write = b'bla\n'
        content_check = 'bla\n'
        file_patch = "/test_read.txt"

        self.storage.write_file(file_patch, self.client_id, content_to_write, self.endpoint)
        content = ''

        for chunk in self.storage.read_file(file_patch, self.client_id, self.endpoint):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            content += chunk.decode('utf-8')

        self.assertEqual(content, content_check, 'File ' + file_patch + ' should contain the string: ' + content_check)

        self.storage.remove(file_patch, self.client_id, self.endpoint)

    def test_read_file_no_file(self):

        file_patch = "/test_read_no_existing_file.txt"
        content = ''

        with self.assertRaises(IOError, msg='No such file or directory'):
            for chunk in self.storage.read_file(file_patch, self.client_id, self.endpoint):
                content += chunk.decode('utf-8')

    def test_write_file(self):

        buffer = b"Testu form cs3 Api"
        file_id = "/testfile.txt"

        self.storage.write_file(file_id, self.client_id, buffer, self.endpoint)

        stat_info = self.storage.stat(file_id, self.client_id, self.endpoint)
        self.assertIsInstance(stat_info, dict)

        self.storage.remove(file_id, self.client_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(file_id, self.client_id, self.endpoint)

    def test_write_empty_file(self):

        buffer = b""
        file_id = "/zero_test_file.txt"

        self.storage.write_file(file_id, self.client_id, buffer, self.endpoint)

        stat_info = self.storage.stat(file_id, self.client_id, self.endpoint)
        self.assertIsInstance(stat_info, dict)

        self.storage.remove(file_id, self.client_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(file_id, self.client_id, self.endpoint)

    def test_write_example(self):

        buffer = b"Example from cs3 API (Test X22)"
        file_id = "/example1.txt"
        self.storage.write_file(file_id, self.client_id, buffer, self.endpoint)

        buffer = b"Example2 from cs3 API"
        file_id = "/example2.txt"
        self.storage.write_file(file_id, self.client_id, buffer, self.endpoint)

        buffer = b'{\
					"cells": [\
						{\
							"cell_type": "markdown",\
							"metadata": {},\
							"source": [\
								"### Markdown example"\
							]\
						}\
					],\
					"metadata": {\
						"kernelspec": {\
							"display_name": "Python 3",\
							"language": "python",\
							"name": "python3"\
						},\
						"language_info": {\
							"codemirror_mode": {\
								"name": "ipython",\
								"version": 3\
							},\
							"file_extension": ".py",\
							"mimetype": "text/x-python",\
							"name": "python",\
							"nbconvert_exporter": "python",\
							"pygments_lexer": "ipython3",\
							"version": "3.7.4"\
						}\
					},\
					"nbformat": 4,\
					"nbformat_minor": 4\
					}'
        file_id = "/note1.ipynb"
        self.storage.write_file(file_id, self.client_id, buffer, self.endpoint)

    def test_remove_file(self):
        file_id = "/file_to_remove.txt"
        buffer = b"ebe5tresbsrdthbrdhvdtr"

        self.storage.write_file(file_id, self.client_id, buffer, self.endpoint)

        self.storage.remove(file_id, self.client_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(file_id, self.client_id, self.endpoint)

    def test_read_directory(self):

        file_id = "/"
        read_directory = self.storage.read_directory(file_id, self.client_id, self.endpoint)
        self.assertIsNotNone(read_directory[0])
        self.assertIsNotNone(read_directory[0].path)

    def test_move_file(self):

        src_id = "/file_to_rename.txt"
        buffer = b"ebe5tresbsrdthbrdhvdtr"

        dest_id = "/file_after_rename.txt"

        self.storage.write_file(src_id, self.client_id, buffer, self.endpoint)
        self.storage.move(src_id, dest_id, self.client_id, self.endpoint)

        self.storage.remove(dest_id, self.client_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(dest_id, self.client_id, self.endpoint)

    def test_read_directory(self):

        fileid = "/"
        read_directory = self.storage.read_directory(fileid, self.userid, self.endpoint)
        self.assertIsNotNone(read_directory[0])
        self.assertIsNotNone(read_directory[0].path)

    def test_move_file(self):

        src_id = "/file_to_rename.txt"
        buffer = b"ebe5tresbsrdthbrdhvdtr"

        dest_id = "/file_after_rename.txt"

        self.storage.write_file(src_id, self.userid, buffer, self.endpoint)
        self.storage.move(src_id, dest_id, self.userid, self.endpoint)

        self.storage.remove(dest_id, self.userid, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(dest_id, self.userid, self.endpoint)

if __name__ == '__main__':
    unittest.main()
