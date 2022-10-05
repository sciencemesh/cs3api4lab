import urllib.parse

import cs3.ocm.provider.v1beta1.provider_api_pb2_grpc as ocm_provider_api_grpc
import cs3.storage.provider.v1beta1.resources_pb2 as Resources

from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.common.strings import *
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.api.cs3_user_api import Cs3UserApi

from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.api.cs3_ocm_share_api import Cs3OcmShareApi

from cs3api4lab.utils.share_utils import ShareUtils
from cs3api4lab.utils.model_utils import ModelUtils
from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.api.storage_api import StorageApi
from cs3api4lab.exception.exceptions import OCMDisabledError

class ShareAPIFacade:
    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        self.file_api = Cs3FileApi(log)

        channel = ChannelConnector().get_channel()
        self.provider_api = ocm_provider_api_grpc.ProviderAPIStub(channel)
        self.user_api = Cs3UserApi(log)

        self.share_api = Cs3ShareApi(log)
        self.ocm_share_api = Cs3OcmShareApi(log)

        self.storage_api = StorageApi(log)
        return

    def create(self, endpoint, file_path, opaque_id, idp, role=Role.EDITOR, grantee_type=Grantee.USER, reshare=True):
        """Creates a share or creates an OCM share if the user is not found in local domain"""
        file_path = FileUtils.normalize_path(file_path)
        if self._is_ocm_user(opaque_id, idp):
            if self.config.enable_ocm:
                return self.ocm_share_api.create(opaque_id, idp, idp, endpoint, file_path, grantee_type, role, reshare)
            else:
                raise OCMDisabledError('Cannot create OCM share - OCM functionality is disabled')
        else:
            return self.share_api.create(endpoint, file_path, opaque_id, idp, role, grantee_type)

    def get_share_received_role(self, path):
        """Check if share has viewer or editor permissions"""
        share = self.share_api.get_share_received(path)

        role = None
        if share:
            role = ShareUtils.map_permissions_to_role(share.permissions.permissions)

        return role

    def update_share(self, params):
        """Updates a field of a share
            Paramterers:
                :param share_id
                :param role: EDITOR/VIEWER
            Parameters for OCM:
                :param share_id
                :param permissions: EDITOR/VIEWER or
                :param display_name
        """
        if self.is_share(params['share_id']):
            self.share_api.update(params['share_id'], params['role'])
        else:
            if not self.config.enable_ocm:
                raise OCMDisabledError('Cannot update OCM share - OCM functionality is disabled')
            else:
                self.ocm_share_api.update(
                    params['share_id'],
                    'permissions',
                    [params['role'], 'role']
                )

    def update_received(self, share_id, state):
        """Updates share's state
           :param share_id
           :param state: accepted/rejected/pending/invalid
        """
        if self.is_ocm_received_share(share_id):
            if self.config.enable_ocm:
                result = self.ocm_share_api.update_received(share_id, 'state', state)
            else:
                raise OCMDisabledError('Cannot update received OCM share - OCM functionality is disabled')
        else:
            result = self.share_api.update_received(share_id, state)

        stat = self.file_api.stat_info(urllib.parse.unquote(result.share.resource_id.opaque_id),
                                       result.share.resource_id.storage_id)  # todo remove this and use storage_logic
        return ModelUtils.map_share_to_base_model(result.share, stat)

    def remove(self, share_id):
        """Removes a share with given opaque_id """

        if self.is_share(share_id):
            self.share_api.remove(share_id)
        else:
            if self.config.enable_ocm:
                return self.ocm_share_api.remove(share_id)
            else:
                raise OCMDisabledError('Cannot remove OCM share - OCM functionality is disabled')

    def list_shares(self, filter_duplicates=False):
        """
        :return: created shares and OCM shares combined and mapped to Jupyter model
        :param: filter_duplicates - wether to filter out duplicated shares by resource id
        :rtype: dict
        """
        share_list = self.share_api.list()
        if self.config.enable_ocm:
            ocm_share_list = self.ocm_share_api.list()
        else:
            ocm_share_list = None
        mapped_shares = self.map_shares(share_list, ocm_share_list)
        if filter_duplicates:
            mapped_shares = self._filter_duplicates(mapped_shares)
        return mapped_shares

    def _filter_duplicates(self, shares):
        resource_ids = []
        filtered_shares = []
        for share in shares['content']:
            if share['resource_id'] not in resource_ids:
                filtered_shares.append(share)
                resource_ids.append(share['resource_id'])
        shares['content'] = filtered_shares
        return shares


    def list_received(self, status=None, path=None):
        """
        :return: received shares and OCM received shares combined and mapped to Jupyter model
        :rtype: dict
        """

        share_list = self.share_api.list_received(path)
        if self.config.enable_ocm:
            ocm_share_list = self.ocm_share_api.list_received()
        else:
            ocm_share_list = None

        mapped_shares = self.map_shares(share_list, ocm_share_list, True)
        if status is not None:
            mapped_shares['content'] = list(filter(lambda share: share['state'] == status, mapped_shares['content']))

        return mapped_shares

    def list_grantees_for_file(self, file_path):
        """
        :param file_path: path to the file
        :return: list of grantees
        """

        file_path = FileUtils.normalize_path(file_path)
        file_path = FileUtils.check_and_transform_file_path(file_path)

        all_shares_list = []
        share_list = self.share_api.list(file_path)
        all_shares_list.extend(share_list.shares)

        if self.config.enable_ocm:
            ocm_share_list = self.ocm_share_api.list(file_path)
            all_shares_list.extend(ocm_share_list.shares)

        shares = []
        for share in all_shares_list:
            shares.append(ShareUtils.get_share_info(share))

        return {"file_path": file_path, "shares": shares}



    def _token(self):
        return [('x-access-token', self.auth.authenticate())]

    def _is_ocm_user(self, opaque_id, idp):
        """Checks if user is present in local provider"""
        return not bool(self.user_api.get_user_info(idp, opaque_id))

    def is_share(self, opaque_id):
        try:
            self.share_api.get(opaque_id)
        except Exception:
            return False

        return True

    def is_ocm_share(self, share_id):
        """Checks if share is present on shares list"""
        for share in self.share_api.list().shares:
            if share.id.opaque_id == share_id:
                return False
        return True

    def is_ocm_received_share(self, share_id):
        """Checks if share is present on OCM received shares list"""
        if self.config.enable_ocm:
            try:
                # if OCM is not enabled on IOP side this call will fail
                received_shares = self.ocm_share_api.list_received()
                for share in received_shares.shares:
                    if share_id == share.share.id.opaque_id:
                        return True
            except Exception as e:
                self.log.error("Error checking OCM " + str(e))
        return False

    def map_shares(self, share_list, ocm_share_list, received=False):
        """Converts both types of shares into Jupyter model"""
        share_list_mapped = self.map_shares_to_model(share_list, received)
        if ocm_share_list:
            ocm_share_list_mapped = self.map_shares_to_model(ocm_share_list, received)
            for share in ocm_share_list_mapped['content']:
                share_list_mapped['content'].append(share)
        return share_list_mapped

    def map_shares_to_model(self, list_response, received=False):
        respond_model = ModelUtils.create_respond_model()
        share_no = 0
        for share in list_response.shares:
            if received:
                share = share.share
            try:
                user = self.user_api.get_user_info(share.owner.idp, share.owner.opaque_id)
                stat = self.file_api.stat_info(urllib.parse.unquote(share.resource_id.opaque_id),
                                               share.resource_id.storage_id)  # todo remove this and use storage_logic
                # stat = self.storage_logic.stat_info(urllib.parse.unquote(share.resource_id.opaque_id), share.resource_id.storage_id)

                if stat['type'] == Resources.RESOURCE_TYPE_FILE:
                    if hasattr(share.permissions.permissions,
                               'initiate_file_download') and share.permissions.permissions.initiate_file_download is False:
                        continue
                    model = ModelUtils.map_share_to_file_model(share, stat, optional={
                        'owner': user['display_name']
                    })
                else:
                    if hasattr(share.permissions.permissions,
                               'list_container') and share.permissions.permissions.list_container is False:
                        continue
                    model = ModelUtils.map_share_to_dir_model(share, stat, optional={
                        'owner': user['display_name']
                    })
                model['writable'] = True if ShareUtils.map_permissions_to_role(
                    share.permissions.permissions) == 'editor' else False
            except Exception as e:
                self.log.error("Unable to map share " + share.resource_id.opaque_id + ", " + e.__str__())
                continue

            if received:
                model['state'] = ShareUtils.map_state(list_response.shares[share_no].state)
            model['resource_id'] = {'storage_id': share.resource_id.storage_id,
                                    'opaque_id': share.resource_id.opaque_id}
            respond_model['content'].append(model)
            share_no = share_no + 1

        return respond_model
