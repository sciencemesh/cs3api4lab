"""
cs3_file_api.py

CS3 File API for the JupyterLab Extension

Authors:
"""


class Cs3FileApi:
	def __init__(self):
		return

	def stat(self, endpoint, fileid, userid):
		return

	def stat_x(self, endpoint, fileid, userid):
		return

	def set_x_attr(self, endpoint, filepath, userid, key, value):
		return

	def get_x_attr(self, endpoint, filepath, userid, key):
		return

	def remove_x_attr(self, endpoint, filepath, userid, key):
		return

	def read_file(self, endpoint, filepath, userid):
		return

	def write_file(self, endpoint, filepath, userid, content, noversion=0):
		return

	def remove_file(self, endpoint, filepath, userid, force=0):
		return
