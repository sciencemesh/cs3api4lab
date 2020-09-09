from unittest import TestCase

from tornado import web

from cs3api_test_ext.api.cs3apismanager import CS3APIsManager
from cs3api_test_ext.api.cs3_file_api import Cs3FileApi
from cs3api_test_ext.config.config_manager import ConfigManager
from traitlets.config import LoggingConfigurable


class TestCS3APIsManager(TestCase, LoggingConfigurable):
    user_id = None
    endpoint = None
    storage = None
    contents_manager = None

    def setUp(self):
        config = ConfigManager('test.conf').config
        self.user_id = config['client_id']
        self.endpoint = config['endpoint']
        self.storage = Cs3FileApi(config, self.log)
        self.contents_manager = CS3APIsManager(self, self.log, config)

    def test_get_text_file(self):

        file_id = "/test_get_text_file.txt"
        message = "Lorem ipsum dolor sit amet..."
        self.storage.write_file(file_id, self.user_id, message, self.endpoint)

        model = self.contents_manager.get(file_id, True, None)

        self.assertEqual(model["name"], "test_get_text_file.txt")
        self.assertEqual(model["path"], file_id)
        self.assertEqual(model["content"], message)
        self.assertEqual(model["format"], "text")
        self.assertEqual(model["mimetype"], "text/plain")
        self.assertEqual(model["size"], 29)
        self.assertEqual(model["writable"], True)
        self.assertEqual(model["type"], "file")

        self.storage.remove(file_id, self.user_id, self.endpoint)

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

        self.storage.write_file(file_id, self.user_id, buffer, self.endpoint)

        model = self.contents_manager.get(file_id, True, "notebook")

        self.assertEqual(model["name"], "test_get_notebook_file.ipynb")
        self.assertEqual(model["path"], file_id)
        self.assertTrue("### Markdown example" in str(model["content"]))
        self.assertEqual(model["format"], "json")
        self.assertEqual(model["mimetype"], None)
        self.assertEqual(model["size"], 637)
        self.assertEqual(model["writable"], True)
        self.assertEqual(model["type"], "notebook")

        self.storage.remove(file_id, self.user_id, self.endpoint)

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
        self.assertEqual(save_model["writable"], True)
        self.assertEqual(save_model["type"], "file")

        self.storage.remove(file_id, self.user_id, self.endpoint)

    def test_save_notebook_model(self):

        file_id = "/test_save_notebook_model.ipynb"
        model = self._create_notebook_model()

        save_model = self.contents_manager.save(model, file_id)

        self.assertEqual(save_model["name"], "test_save_notebook_model.ipynb")
        self.assertEqual(save_model["path"], file_id)
        self.assertEqual(save_model["content"], None)
        self.assertEqual(save_model["format"], None)
        self.assertEqual(save_model["mimetype"], None)
        self.assertEqual(save_model["size"], 521)
        self.assertEqual(save_model["writable"], True)
        self.assertEqual(save_model["type"], "notebook")

        self.storage.remove(file_id, self.user_id, self.endpoint)

    def _create_notebook_model(self):
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
        return model

    def test_delete_file(self):

        file_path = "/test_delete_exits_file.txt"
        message = "Lorem ipsum dolor sit amet..."
        self.storage.write_file(file_path, self.user_id, message, self.endpoint)

        self.contents_manager.delete_file(file_path)

        with self.assertRaises(IOError):
            self.storage.stat(file_path, self.user_id, self.endpoint)

    def test_delete_non_exits_file(self):

        file_path = "/test_delete_non_exits_file.txt"

        with self.assertRaises(web.HTTPError):
            self.contents_manager.delete_file(file_path)

    def test_rename_file(self):

        file_path = "/test_rename_file.txt"
        message = "Lorem ipsum dolor sit amet..."
        self.storage.write_file(file_path, self.user_id, message, self.endpoint)

        file_dest = "/test_after_rename_file.txt"

        self.contents_manager.rename_file(file_path, file_dest)

        stat_info = self.storage.stat(file_dest, self.user_id, self.endpoint)
        self.assertIsInstance(stat_info, dict)

        with self.assertRaises(IOError):
            self.storage.stat(file_path, self.user_id, self.endpoint)

        self.storage.remove(file_dest, self.user_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(file_dest, self.user_id, self.endpoint)


    def test_rename_file_non_exits_file(self):

        file_path = "/test_rename_file.txt"
        file_dest = "/test_after_rename_file.txt"

        with self.assertRaises(web.HTTPError):
            self.contents_manager.rename_file(file_path, file_dest)

    def test_new_file_model(self):

        file_path = "/test_new_file_model.txt"
        model = {
            "type": "file",
            "format": "text",
            "content": "Test content",
        }

        self.contents_manager.new(model, file_path)

        model = self.contents_manager.get(file_path, True, None)
        self.assertEqual(model["name"], "test_new_file_model.txt")
        self.assertEqual(model["path"], file_path)
        self.assertEqual(model["content"], "Test content")
        self.assertEqual(model["format"], "text")
        self.assertEqual(model["mimetype"], "text/plain")
        self.assertEqual(model["size"], 12)
        self.assertEqual(model["writable"], True)
        self.assertEqual(model["type"], "file")

        self.storage.remove(file_path, self.user_id, self.endpoint)

    def test_new_notebook_model(self):

        file_path = "/test_new_notebook_model.ipynb"
        model = self._create_notebook_model()

        save_model = self.contents_manager.new(model, file_path)

        self.assertEqual(save_model["name"], "test_new_notebook_model.ipynb")
        self.assertEqual(save_model["path"], file_path)
        self.assertEqual(save_model["content"], None)
        self.assertEqual(save_model["format"], None)
        self.assertEqual(save_model["mimetype"], None)
        self.assertEqual(save_model["size"], 521)
        self.assertEqual(save_model["writable"], True)
        self.assertEqual(save_model["type"], "notebook")

        self.storage.remove(file_path, self.user_id, self.endpoint)


    def test_file_exits(self):

        file_path = "/test_file_exits.txt"
        message = "Lorem ipsum dolor sit amet..."
        self.storage.write_file(file_path, self.user_id, message, self.endpoint)

        file_exists = self.contents_manager.file_exists(file_path)
        self.assertTrue(file_exists)

        self.storage.remove(file_path, self.user_id, self.endpoint)
        with self.assertRaises(IOError):
            self.storage.stat(file_path, self.user_id, self.endpoint)

        file_exists = self.contents_manager.file_exists(file_path)
        self.assertFalse(file_exists)

    def test_is_hidden(self):

        file_path = "/.test_hidden_file3.txt"
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertTrue(is_hidden)

        file_path = "/test_dir/.test_hidden_file3.txt"
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertTrue(is_hidden)

        file_path = "/.test_dir/file.txt"
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertTrue(is_hidden)

        file_path = "/root_dir/.test_dir/file.txt"
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertTrue(is_hidden)

        file_path = "/test_normal_file.txt"
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertFalse(is_hidden)

        file_path = "/test_dir/test_normal_file.txt"
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertFalse(is_hidden)

        file_path = "/test_dir/file.txt"
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertFalse(is_hidden)

        file_path = "/root_dir/test_dir/file.txt"
        is_hidden = self.contents_manager.is_hidden(file_path)
        self.assertFalse(is_hidden)

    def test_create_directory(self):

        file_path = "/test_create_directory"
        self.storage.create_directory(file_path, self.user_id, self.endpoint)

        self.contents_manager.delete_file(file_path)

        with self.assertRaises(IOError):
            self.storage.stat(file_path, self.user_id, self.endpoint)

    def test_recreate_directory(self):

        file_path = "/test_recreate_directory"
        self.storage.create_directory(file_path, self.user_id, self.endpoint)

        with self.assertRaises(IOError):
            self.storage.create_directory(file_path, self.user_id, self.endpoint)

        self.contents_manager.delete_file(file_path)

        with self.assertRaises(IOError):
            self.storage.stat(file_path, self.user_id, self.endpoint)


    def test_create_subdirectory(self):

        file_path = "/test_create_directory"
        self.storage.create_directory(file_path, self.user_id, self.endpoint)

        file_path2 = "/test_create_directory/test_subdir"
        self.storage.create_directory(file_path2, self.user_id, self.endpoint)

        self.contents_manager.delete_file(file_path2)
        with self.assertRaises(IOError):
            self.storage.stat(file_path2, self.user_id, self.endpoint)

        self.contents_manager.delete_file(file_path)
        with self.assertRaises(IOError):
            self.storage.stat(file_path, self.user_id, self.endpoint)
