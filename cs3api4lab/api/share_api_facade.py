import mimetypes

from datetime import datetime
from IPython.utils import tz
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.common.strings import *
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.api.cs3_user_api import Cs3UserApi

from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi
from cs3api4lab.api.share_utils import ShareUtils

import urllib.parse


class ShareAPIFacade:
    date_fmt = '%Y-%m-%dT%H:%M:%SZ'
    TYPE_FILE = 1
    TYPE_DIRECTORY = 2

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        self.file_api = Cs3FileApi(log)
        self.user_api = Cs3UserApi(log)
        self.share_api = Cs3ShareApi(log)
        self.ocm_share_api = Cs3OcmShareApi(log)
        return

    def create(self, endpoint, file_path, opaque_id, idp, role=Role.EDITOR, grantee_type=Grantee.USER, reshare=True):
        """Creates a share or creates an OCM share if the user is not found in local domain"""
        # We still don't know if it's an OCM share, but we should not check if it has been disabled in the config
        # It will fail either way
        if self._check_ocm_enabled(just_warning=True) and self._is_ocm_user(opaque_id, idp):
            return self.ocm_share_api.create(opaque_id, idp, idp, endpoint, file_path, grantee_type, role, reshare)
        else:
            return self.share_api.create(endpoint, file_path, opaque_id, idp, role, grantee_type)

    def update_share(self, **kwargs):
        """Updates a field of a share
        Paramterers:
            :param share_id
            :param role: EDITOR/VIEWER
        Parameters for OCM:
            :param share_id
            :param permissions: EDITOR/VIEWER or
            :param display_name
        """
        if 'role' in kwargs:
            self.share_api.update(kwargs['share_id'], kwargs['role'])
        else:
            self._check_ocm_enabled()
            self.ocm_share_api.update(kwargs['share_id'], kwargs['field'], kwargs['value'])

    def update_received(self, share_id, state):
        """Updates share's state
        :param share_id
        :param state: accepted/rejected/pending/invalid
        """
        if self._is_ocm_received_share(share_id):
            self._check_ocm_enabled()
            self.ocm_share_api.update_received(share_id, 'state', state)
        else:
            self.share_api.update_received(share_id, state)

    def remove(self, share_id):
        """Removes a share with given id """
        if self._check_ocm_enabled(just_warning=True) and self._is_ocm_share(share_id):
            return self.ocm_share_api.remove(share_id)
        else:
            return self.share_api.remove(share_id)

    def list_shares(self):
        """
        :return: created shares and OCM shares combined and mapped to Jupyter model
        :rtype: dict
        """
        share_list = self.share_api.list()
        if self._check_ocm_enabled(just_warning=True):
            ocm_share_list = self.ocm_share_api.list()
        else:
            ocm_share_list = None
        return self.map_shares(share_list, ocm_share_list)

    def list_received(self):
        """
        :return: received shares and OCM received shares combined and mapped to Jupyter model
        :rtype: dict
        """
        share_list = self.share_api.list_received()
        if self._check_ocm_enabled(just_warning=True):
            ocm_share_list = self.ocm_share_api.list_received()
        else:
            ocm_share_list = None
        return self.map_shares(share_list, ocm_share_list, True)

    def list_grantees_for_file(self, file_path):
        """
        :param file_path: path to the file
        :return: list of grantees
        """
        share_list = self.share_api.list()

        if self._check_ocm_enabled(just_warning=True):
            ocm_share_list = self.ocm_share_api.list()
        else:
            ocm_share_list = {shares: []}

        file_path = ShareUtils.purify_file_path(file_path, self.config['client_id'])
        shares = []
        for share in [*share_list.shares, *ocm_share_list.shares]:
            path = ShareUtils.purify_file_path(share.resource_id.opaque_id, self.config['client_id'])
            if file_path == path:
                shares.append(self._get_share_info(share))

        response = {"file_path": file_path, "shares": shares}
        return response

    def _get_share_info(self, share):
        return {
            "opaque_id": share.id.opaque_id,
            "grantee": {
                "idp": share.grantee.user_id.idp,
                "opaque_id": share.grantee.user_id.opaque_id,
                "permissions": ShareUtils.map_permissions_to_role(share.permissions.permissions)
            }
        }

    def _token(self):
        return [('x-access-token', self.auth.authenticate())]

    def _is_ocm_user(self, opaque_id, idp):
        """Checks if user is present in local provider"""
        return not bool(self.user_api.get_user_info(idp, opaque_id))

    def _is_ocm_share(self, share_id):
        """Checks if share is present on OCM shares list"""
        return self.ocm_share_api.list(share_id)['id'] != ''

    def _is_ocm_received_share(self, share_id):
        """Checks if share is present on OCM received shares list"""
        return self.ocm_share_api.get_received_ocm_shares(share_id)['id'] != ''

    def _check_ocm_enabled(self, just_warning=False):
        if not self.config['enable_ocm']:
            if not just_warning:
                raise Exception('Received OCM request bug functionality is disabled')
            return False
        return True

    def map_shares(self, share_list, ocm_share_list, received=False):
        """Converts both types of shares into Jupyter model"""
        share_list_mapped = self.map_shares_to_model(share_list, received)
        if ocm_share_list: 
            ocm_share_list_mapped = self.map_shares_to_model(ocm_share_list, received)
            for share in ocm_share_list_mapped['content']:
                share_list_mapped['content'].append(share)
        return share_list_mapped

    def map_shares_to_model(self, list_response, received=False):
        respond_model = self._create_respond_model()
        path_list = []
        share_no = 0
        for share in list_response.shares:
            if received:
                share = share.share
            try:
                stat = self.file_api.stat(urllib.parse.unquote(share.resource_id.opaque_id), share.resource_id.storage_id)

                if stat['type'] == self.TYPE_FILE:
                    if hasattr(share.permissions.permissions,
                               'initiate_file_download') and share.permissions.permissions.initiate_file_download is False:
                        continue
                    model = self._map_share_to_file_model(share, stat)
                else:
                    if hasattr(share.permissions.permissions,
                               'list_container') and share.permissions.permissions.list_container is False:
                        continue
                    model = self._map_share_to_dir_model(share, stat)
                model['writable'] = True if ShareUtils.map_permissions_to_role(share.permissions.permissions) == 'editor' else False
            except:
                model = {'name': share.resource_id.opaque_id.rsplit('/', 1)[-1],
                         'path': share.resource_id.opaque_id,
                         'last_modified': '',
                         'created': '',
                         'content': None,
                         'format': None,
                         'writable': False,
                         'size': 13,
                         'type': 'file',
                         'mimetype': 'text/plain'}
            if received:
                model['accepted'] = ShareUtils.is_accepted(list_response.shares[share_no].state)
            if model['path'] not in path_list:
                respond_model['content'].append(model)
                path_list.append(model['path'])
                share_no = share_no + 1

        return respond_model

    def _create_respond_model(self):

        model = {}
        model['name'] = "/"
        model['path'] = "/"
        model['last_modified'] = datetime.now(tz=tz.UTC).strftime(self.date_fmt)
        model['created'] = datetime.now(tz=tz.UTC).strftime(self.date_fmt)
        model['mimetype'] = None
        model['writable'] = False
        model['type'] = None
        model['size'] = None
        model['type'] = 'directory'
        model['content'] = []
        model['format'] = 'json'

        return model

    def _map_share_to_base_model(self, share, stat):

        created = datetime.fromtimestamp(share.ctime.seconds, tz=tz.UTC).strftime(self.date_fmt)
        last_modified = datetime.fromtimestamp(share.mtime.seconds, tz=tz.UTC).strftime(self.date_fmt)

        writable = False
        if hasattr(share.permissions.permissions,
                   'initiate_file_upload') and share.permissions.permissions.initiate_file_upload is True:
            writable = True

        model = {}
        model['name'] = stat['filepath'].rsplit('/', 1)[-1]
        model['path'] = stat['filepath']
        model['last_modified'] = last_modified
        model['created'] = created
        model['content'] = None
        model['format'] = None
        model['writable'] = writable
        return model

    def _map_share_to_file_model(self, share, stat):

        model = self._map_share_to_base_model(share, stat)
        model['size'] = stat['size']
        model['type'] = 'file'
        model['mimetype'] = mimetypes.guess_type(stat['filepath'])[0]

        return model

    def _map_share_to_dir_model(self, share, stat):

        model = self._map_share_to_base_model(share, stat)
        model['size'] = None
        model['type'] = 'directory'
        model['mimetype'] = None
        return model
