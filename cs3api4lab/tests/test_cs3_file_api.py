import unittest
from unittest import TestCase

import logging
import configparser

from cs3api4lab.cs3_file_api import Cs3FileApi


class TestCs3FileApi(TestCase):

    userid = None
    endpoint = None

    def setUp(self):

        log_handler = logging.FileHandler('/var/tmp/cs3api.log')
        log_handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(name)s[%(process)d] %(levelname)-8s %(message)s',
                                                   datefmt='%Y-%m-%dT%H:%M:%S'))
        log = logging.getLogger('cs3api.test')
        log.addHandler(log_handler)
        log.setLevel(logging.DEBUG)

        config_parser = configparser.ConfigParser()

        try:
            with open('test.conf') as fdconf:
                config_parser.read_file(fdconf)

            self.userid = config_parser.get('cs3', 'userid')
            self.endpoint = config_parser.get('cs3', 'endpoint')

            config = {
                "revahost": config_parser.get('cs3', 'revahost'),
                "authtokenvalidity": config_parser.get('cs3', 'authtokenvalidity'),
                "userid": config_parser.get('cs3', 'userid'),
                "endpoint": config_parser.get('cs3', 'endpoint'),
                "secure_channel": config_parser.getboolean('cs3', 'secure_channel'),
                "client_cert": config_parser.get('cs3', 'client_cert'),
                "client_key": config_parser.get('cs3', 'client_key'),
                "ca_cert": config_parser.get('cs3', 'ca_cert'),
                "chunksize": config_parser.get('io', 'chunksize'),
                "client_id": config_parser.get('cs3', 'client_id'),
                "client_secret": config_parser.get('cs3', 'client_secret'),
            }

            self.storage = Cs3FileApi(config, log)

        except (KeyError, configparser.NoOptionError):
            print("Missing option or missing configuration, check the test.conf file")
            raise

    def test_stat(self):

        fileid = "/test.txt"
        message = "Lorem ipsum dolor sit amet..."

        self.storage.write_file(self.endpoint, fileid, self.userid, message)

        stat_info = self.storage.stat(self.endpoint, fileid, self.userid)

        self.assertIsInstance(stat_info, dict)
        self.assertTrue('mtime' in stat_info, 'Missing mtime from stat output')
        self.assertTrue('size' in stat_info, 'Missing size from stat output')

        self.storage.remove(self.endpoint, fileid, self.userid)

    def test_stat_no_file(self):
        with self.assertRaises(IOError, msg='No such file or directory'):
            self.storage.stat(self.endpoint, '/hopefullynotexisting', self.userid)

    def test_read_file(self):

        content_to_write = b'bla\n'
        content_check = 'bla\n'
        file_patch = "/test_read.txt"

        self.storage.write_file(self.endpoint, file_patch, self.userid, content_to_write)
        content = ''

        for chunk in self.storage.read_file(self.endpoint, file_patch, self.userid):
            self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
            content += chunk.decode('utf-8')

        self.assertEqual(content, content_check, 'File ' + file_patch + ' should contain the string: ' + content_check)

        self.storage.remove(self.endpoint, file_patch, self.userid)

    def test_read_file_no_file(self):

        file_patch = "/test_read_no_existing_file.txt"
        content = ''

        with self.assertRaises(IOError, msg='No such file or directory'):
            for chunk in self.storage.read_file(self.endpoint, file_patch, self.userid):
                content += chunk.decode('utf-8')

    def test_write_file(self):

        buffer = b"Testu form cs3 Api"
        fileid = "/testfile.txt"

        self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

        stat_info = self.storage.stat(self.endpoint, fileid, self.userid)
        self.assertIsInstance(stat_info, dict)

        self.storage.remove(self.endpoint, fileid, self.userid)
        with self.assertRaises(IOError):
            self.storage.stat(self.endpoint, fileid, self.userid)


    def test_write_example(self):

        buffer = b"Example from cs3 API"
        fileid = "/example1.txt"
        self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

        buffer = b"Example2 from cs3 API"
        fileid = "/example2.txt"
        self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

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
        self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

    def test_remove_file(self):
        fileid = "/file_to_remove.txt"
        buffer = b"ebe5tresbsrdthbrdhvdtr"

        self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

        self.storage.remove(self.endpoint, fileid, self.userid)
        with self.assertRaises(IOError):
            self.storage.stat(self.endpoint, fileid, self.userid)


if __name__ == '__main__':
    unittest.main()
