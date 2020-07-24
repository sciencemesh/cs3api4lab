import unittest
from unittest import TestCase

import logging
import configparser

from cs3api_test_ext.cs3_file_api import Cs3FileApi


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

		config_parser = configparser.ConfigParser()

		try:
			with open('test.conf') as fdconf:
				config_parser.read_file(fdconf)
			self.userid = config_parser.get('cs3', 'userid')
			self.endpoint = config_parser.get('cs3', 'endpoint')
		except (KeyError, configparser.NoOptionError):
			print("Missing option or missing configuration, check the test.conf file")
			raise

		config = {
			"revahost": config_parser.get('cs3', 'revahost'),
			"authtokenvalidity": config_parser.get('cs3', 'authtokenvalidity'),
			"userid": config_parser.get('cs3', 'userid'),
			"endpoint": config_parser.get('cs3', 'endpoint'),
			"chunksize": config_parser.get('io', 'chunksize')
		}

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


	def test_write_example(self):

		buffer = b"Example from cs3 API"
		fileid = "/example1.txt"
		self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

		buffer = b"Example2 from cs3 API"
		fileid = "/example2.txt"
		self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

		buffer = b"Example3 from cs3 API"
		fileid = "/example3.txt"
		self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

		buffer = b"Example4 from cs3 API"
		fileid = "/example4.txt"
		self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

		buffer = b"Example5 from cs3 API"
		fileid = "/example5.txt"
		self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

		buffer = b"Example6 from cs3 API"
		fileid = "/example6.txt"
		self.storage.write_file(self.endpoint, fileid, self.userid, buffer)

		buffer = b"Example7 from cs3 API"
		fileid = "/example7.txt"
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

		self.storage.remove_file(self.endpoint, fileid, self.userid)
		with self.assertRaises(IOError):
			self.storage.stat(self.endpoint, fileid, self.userid)

	def test_read_directory(self):

		"""
		[type: RESOURCE_TYPE_FILE
		id {
			storage_id: "123e4567-e89b-12d3-a456-426655440000"
			opaque_id: "fileid-%2Fexample1.txt"
		}
		etag: "\"433b3efae4d700628204b60fb7207787\""
		mime_type: "text/plain; charset=utf-8"
		mtime {
			seconds: 1594195752
		}
		path: "/example1.txt"
		permission_set {
			create_container: true
			list_container: true
		}
		size: 20
		owner {
			idp: "http://cernbox.cern.ch"
			opaque_id: "4c510ada-c86b-4815-8820-42cdf82c3d51"
		}
		arbitrary_metadata {
						   }
		, ......			   }
		, type: RESOURCE_TYPE_CONTAINER
		id {
			storage_id: "123e4567-e89b-12d3-a456-426655440000"
			opaque_id: "fileid-%2Fhome%2FMyShares"
		}
		etag: "\"56fb030b7dc4dfbf9e87fc4ed1ddb14d\""
		mime_type: "httpd/unix-directory"
		mtime {
			seconds: 1593606956
		}
		path: "/home/MyShares"
		permission_set {
			create_container: true
			list_container: true
		}
		size: 512
		owner {
			idp: "http://cernbox.cern.ch"
			opaque_id: "4c510ada-c86b-4815-8820-42cdf82c3d51"
		}
		arbitrary_metadata {
		}
		]
		"""
		fileid = "/"
		read_directory = self.storage.read_directory(self.endpoint, fileid, self.userid)
		self.assertIsNotNone(read_directory[0])
		self.assertIsNotNone(read_directory[0].path)

	#
	# def test_read_directory_my_share(self):
	# 	fileid = "/home/MyShares"
	# 	read_directory = self.storage.read_directory(self.endpoint, fileid, self.userid)
	# 	print(read_directory)
	# 	# self.assertIsNotNone(read_directory[0])
	# 	# self.assertIsNotNone(read_directory[0].path)
	#

	def test_rename_file(self):

		src_id = "/file_to_rename.txt"
		buffer = b"ebe5tresbsrdthbrdhvdtr"

		dest_id = "/file_after_rename.txt"

		self.storage.write_file(self.endpoint, src_id, self.userid, buffer)
		self.storage.move(self.endpoint, src_id, dest_id, self.userid)

		self.storage.remove_file(self.endpoint, dest_id, self.userid)
		with self.assertRaises(IOError):
			self.storage.stat(self.endpoint, dest_id, self.userid)


if __name__ == '__main__':
	unittest.main()
