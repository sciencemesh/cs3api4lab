"""
cs3_share_api.py

CS3 Share API for the JupyterLab Extension

Authors:
"""


class Cs3ShareApi:
	def __init__(self):
		return

	def create(self, endpoint, fileid, userid, grantee, idp=None, role="viewer", grantee_type="user"):
		return

	def list(self, userid):
		return

	def remove(self, endpoint, shareid, userid):
		return

	def update(self, endpoint, shareid, userid, role="viewer"):
		return

	def list_received(self, endpoint, userid):
		return

	def update_received(self, endpoint, shareid, userid, state="pending"):
		return
