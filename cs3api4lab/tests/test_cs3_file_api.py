import unittest
from unittest import TestCase

import logging
import configparser

from cs3api4lab.cs3_file_api import Cs3FileApi


class TestCs3FileApi(TestCase):
	userid = None
	endpoint = None
	storagetype = None

	def setUp(self):

		log_handler = logging.FileHandler('/var/tmp/cs3api.log')
		log_handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(name)s[%(process)d] %(levelname)-8s %(message)s',
												   datefmt='%Y-%m-%dT%H:%M:%S'))
		log = logging.getLogger('cs3api.test')
		log.addHandler(log_handler)
		log.setLevel(logging.DEBUG)

		config = configparser.ConfigParser()

		try:
			with open('test.conf') as fdconf:
				config.read_file(fdconf)
			self.userid = config.get('cs3', 'userid')
			self.endpoint = config.get('cs3', 'endpoint')
		except (KeyError, configparser.NoOptionError):
			print("Missing option or missing configuration, check the test.conf file")
			raise

		self.storage = Cs3FileApi(config, log)

	def test_stat(self):

		fileid = "/test.txt"
		message = "Lorem ipsum dolor sit amet..."

		self.storage.write_file(self.endpoint, fileid, self.userid, message)

		stat_info = self.storage.stat(self.endpoint, fileid, self.userid)

		self.assertIsInstance(stat_info, dict)
		self.assertTrue('mtime' in stat_info, 'Missing mtime from stat output')
		self.assertTrue('size' in stat_info, 'Missing size from stat output')

		self.storage.remove_file(self.endpoint, fileid, self.userid)

	def test_stat_x(self):
		buf = b'bla\n'
		file_path = '/test.txt'

		self.storage.write_file(self.endpoint, file_path, self.userid, buf)
		stat_info = self.storage.stat_x(self.endpoint, file_path, self.userid)
		self.assertIsInstance(stat_info, dict)

		fileid = stat_info['inode'].split(':')
		self.assertEqual(len(fileid), 2, 'This storage interface does not support stat by fileid')

		stat_info = self.storage.stat_x(fileid[0], fileid[1], self.userid)

		self.assertIsInstance(stat_info, dict)

		self.assertEqual(stat_info['filepath'], file_path, 'Filepath should be ' + file_path)
		self.storage.remove_file(self.endpoint, file_path, self.userid)

	def test_stat_no_file(self):
		with self.assertRaises(IOError, msg='No such file or directory'):
			self.storage.stat(self.endpoint, '/hopefullynotexisting', self.userid)

	def test_stat_x_no_file(self):
		with self.assertRaises(IOError, msg='No such file or directory'):
			self.storage.stat_x(self.endpoint, '/hopefullynotexisting', self.userid)

	def test_operation_on_x_attr(self):

		buf = b'bla\n'
		file_path = '/testxattr.txt'

		self.storage.write_file(self.endpoint, file_path, self.userid, buf)
		self.storage.set_x_attr(self.endpoint, file_path, self.userid, 'testkey', 123)

		v = self.storage.get_x_attr(self.endpoint, file_path, self.userid, 'testkey')
		self.assertEqual(v, '123')

		self.storage.remove_x_attr(self.endpoint, file_path, self.userid, 'testkey')
		v = self.storage.get_x_attr(self.endpoint, file_path, self.userid, 'testkey')
		self.assertEqual(v, None)

		self.storage.remove_file(self.endpoint, file_path, self.userid)

	def test_read_file(self):

		content_to_write = b'bla\n'
		content_check = 'bla\n'
		filepatch = "/test_read.txt"

		self.storage.write_file(self.endpoint, filepatch, self.userid, content_to_write)
		content = ''

		for chunk in self.storage.read_file(self.endpoint, filepatch, self.userid):
			self.assertNotIsInstance(chunk, IOError, 'raised by storage.readfile')
			content += chunk.decode('utf-8')

		self.assertEqual(content, content_check, 'File ' + filepatch + ' should contain the string: ' + content_check)

		self.storage.remove_file(self.endpoint, filepatch, self.userid)

	def test_write_file(self):

		buffer = b"Testu form cs3 Api"
		fileid = "/testfile.txt"

		self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

		stat_info = self.storage.stat(self.endpoint, fileid, self.userid)
		self.assertIsInstance(stat_info, dict)

		self.storage.remove_file(self.endpoint, fileid, self.userid)
		with self.assertRaises(IOError):
			self.storage.stat(self.endpoint, fileid, self.userid)

	def test_remove_file(self):
		fileid = "/file_to_remove.txt"
		buffer = b"ebe5tresbsrdthbrdhvdtr"

		self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

		self.storage.remove_file(self.endpoint, fileid, self.userid)
		with self.assertRaises(IOError):
			self.storage.stat(self.endpoint, fileid, self.userid)


if __name__ == '__main__':
	unittest.main()
