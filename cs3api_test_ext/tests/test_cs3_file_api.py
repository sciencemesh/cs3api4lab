import unittest
import logging
from unittest import TestCase
from cs3api_test_ext.config.config_manager import ConfigManager
from cs3api_test_ext.api.cs3_file_api import Cs3FileApi


class TestCs3FileApi(TestCase):
    user_id = None
    endpoint = None

    def setUp(self):

        log = logging.getLogger('cs3api.test')
        log.setLevel(logging.DEBUG)

        config = ConfigManager('test.conf').config

        self.user_id = config['user_id']
        self.endpoint = config['endpoint']
        self.storage = Cs3FileApi(config, log)



    def test_stat(self):

        fileid = "/test.txt"
        message = "Lorem ipsum dolor sit amet..."

        self.storage.write_file(fileid, self.user_id, message, self.endpoint)

        stat_info = self.storage.stat(fileid, self.user_id, self.endpoint)

        self.assertIsInstance(stat_info, dict)
        self.assertTrue('mtime' in stat_info, 'Missing mtime from stat output')
        self.assertTrue('size' in stat_info, 'Missing size from stat output')

        self.storage.remove(fileid, self.user_id, self.endpoint)

    def test_stat_no_file(self):
        with self.assertRaises(IOError, msg='No such file or directory'):
            self.storage.stat('/hopefullynotexisting', self.user_id, self.endpoint)

    def test_read_file(self):

        content_to_write = b'bla\n'
        content_check = 'bla\n'
        file_patch = "/test_read.txt"

        self.storage.write_file(file_patch, self.user_id, content_to_write, self.endpoint)
        content = ''

        for chunk in self.storage.read_file(file_patch, self.user_id, self.endpoint):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            content += chunk.decode('utf-8')

        self.assertEqual(content, content_check, 'File ' + file_patch + ' should contain the string: ' + content_check)

        self.storage.remove(file_patch, self.user_id, self.endpoint)

    def test_read_file_no_file(self):

        file_patch = "/test_read_no_existing_file.txt"
        content = ''

        with self.assertRaises(IOError, msg='No such file or directory'):
            for chunk in self.storage.read_file(file_patch, self.user_id, self.endpoint):
                content += chunk.decode('utf-8')

    def test_write_file(self):

        buffer = b"Testu form cs3 Api"
        fileid = "/testfile.txt"

        self.storage.write_file(fileid, self.user_id, buffer, self.endpoint)

        stat_info = self.storage.stat(fileid, self.user_id, self.endpoint)
        self.assertIsInstance(stat_info, dict)

        self.storage.remove(fileid, self.user_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(fileid, self.user_id, self.endpoint)

    def test_write_empty_file(self):

        buffer = b""
        fileid = "/zero_test_file.txt"

        self.storage.write_file(fileid, self.user_id, buffer, self.endpoint)

        stat_info = self.storage.stat(fileid, self.user_id, self.endpoint)
        self.assertIsInstance(stat_info, dict)

        self.storage.remove(fileid, self.user_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(fileid, self.user_id, self.endpoint)

    def test_write_example(self):

        buffer = b"Example from cs3 API (Test X22)"
        fileid = "/example1.txt"
        self.storage.write_file(fileid, self.user_id, buffer, self.endpoint)

        buffer = b"Example2 from cs3 API"
        fileid = "/example2.txt"
        self.storage.write_file(fileid, self.user_id, buffer, self.endpoint)

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
        fileid = "/note1.ipynb"
        self.storage.write_file(fileid, self.user_id, buffer, self.endpoint)

    def test_remove_file(self):
        fileid = "/file_to_remove.txt"
        buffer = b"ebe5tresbsrdthbrdhvdtr"

        self.storage.write_file(fileid, self.user_id, buffer, self.endpoint)

        self.storage.remove(fileid, self.user_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(fileid, self.user_id, self.endpoint)

    def test_read_directory(self):

        fileid = "/"
        read_directory = self.storage.read_directory(fileid, self.user_id, self.endpoint)
        self.assertIsNotNone(read_directory[0])
        self.assertIsNotNone(read_directory[0].path)

    def test_move_file(self):

        src_id = "/file_to_rename.txt"
        buffer = b"ebe5tresbsrdthbrdhvdtr"

        dest_id = "/file_after_rename.txt"

        self.storage.write_file(src_id, self.user_id, buffer, self.endpoint)
        self.storage.move(src_id, dest_id, self.user_id, self.endpoint)

        self.storage.remove(dest_id, self.user_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(dest_id, self.user_id, self.endpoint)


if __name__ == '__main__':
    unittest.main()
