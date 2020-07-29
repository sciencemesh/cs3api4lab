from unittest import TestCase

import logging
import configparser

from cs3api4lab import CS3APIsManager
from cs3api4lab.cs3_file_api import Cs3FileApi


class TestCS3APIsManager(TestCase):
    userid = None
    endpoint = None
    storage = None
    contents_manager = None

    def setUp(self):

        log = logging.getLogger('cs3api.test')
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
            log.error("Missing option or missing configuration, check the test.conf file")
            raise

        self.contents_manager = CS3APIsManager(self, log)

    def test_get_text_file(self):

        file_id = "/test_get_text_file.txt"
        message = "Lorem ipsum dolor sit amet..."
        self.storage.write_file(file_id, self.userid, message, self.endpoint)

        model = self.contents_manager.get(file_id, True, None)

        self.assertEqual(model["name"], "test_get_text_file.txt")
        self.assertEqual(model["path"], file_id)
        self.assertEqual(model["content"], message)
        self.assertEqual(model["format"], None)
        self.assertEqual(model["mimetype"], "text/plain")
        self.assertEqual(model["size"], 29)
        self.assertEqual(model["writable"], False)
        self.assertEqual(model["type"], "file")

        self.storage.remove(file_id, self.userid, self.endpoint)

    def test_get_notebook_file(self):

        file_id = "/test_get_notebook_file.ipynb"
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

        self.storage.write_file(file_id, self.userid, buffer, self.endpoint)

        model = self.contents_manager.get(file_id, True, "notebook")

        self.assertEqual(model["name"], "test_get_notebook_file.ipynb")
        self.assertEqual(model["path"], file_id)
        self.assertTrue("### Markdown example" in str(model["content"]))
        self.assertEqual(model["format"], "json")
        self.assertEqual(model["mimetype"], None)
        self.assertEqual(model["size"], 637)
        self.assertEqual(model["writable"], False)
        self.assertEqual(model["type"], "notebook")

        self.storage.remove(file_id, self.userid, self.endpoint)

    def test_save_text_model(self):

        file_id = "/test_save_text_model.txt"
        model = {
            "type": "file",
            "format": "text",
            "content": "Test content",
        }

        save_model = self.contents_manager.save(model, file_id)

        self.assertEqual(save_model["name"], "test_save_text_model.txt")
        self.assertEqual(save_model["path"], file_id)
        self.assertEqual(save_model["content"], None)
        self.assertEqual(save_model["format"], None)
        self.assertEqual(save_model["mimetype"], "text/plain")
        self.assertEqual(save_model["size"], 12)
        self.assertEqual(save_model["writable"], False)
        self.assertEqual(save_model["type"], "file")

        self.storage.remove(file_id, self.userid, self.endpoint)

    def test_save_notebook_model(self):

        file_id = "/test_save_notebook_model.ipynb"
        model = {
            "type": "notebook",
            "format": None,
            "content": {
                "nbformat": 4,
                "cells": [
                    {
                        "cell_type": "markdown",
                        "metadata": {},
                        "source": [
                            "### Markdown example"
                        ]
                    }
                ],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3"
                    },
                    "language_info": {
                        "codemirror_mode": {
                            "name": "ipython",
                            "version": 3
                        },
                        "file_extension": ".py",
                        "mimetype": "text/x-python",
                        "name": "python",
                        "nbconvert_exporter": "python",
                        "pygments_lexer": "ipython3",
                        "version": "3.7.4"
                    }
                },
            },
        }

        save_model = self.contents_manager.save(model, file_id)

        self.assertEqual(save_model["name"], "test_save_notebook_model.ipynb")
        self.assertEqual(save_model["path"], file_id)
        self.assertEqual(save_model["content"], None)
        self.assertEqual(save_model["format"], None)
        self.assertEqual(save_model["mimetype"], None)
        self.assertEqual(save_model["size"], 521)
        self.assertEqual(save_model["writable"], False)
        self.assertEqual(save_model["type"], "notebook")

        self.storage.remove(file_id, self.userid, self.endpoint)
