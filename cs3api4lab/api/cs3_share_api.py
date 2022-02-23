"""
cs3_share_api.py

CS3 Share API for the JupyterLab Extension

Authors:
"""
import cs3.sharing.collaboration.v1beta1.collaboration_api_pb2 as sharing
import cs3.sharing.collaboration.v1beta1.resources_pb2 as sharing_res
import cs3.storage.provider.v1beta1.provider_api_pb2 as storage_provider
import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
import cs3.identity.user.v1beta1.resources_pb2 as identity_res
import cs3.rpc.v1beta1.code_pb2 as cs3_code
import grpc

from tornado import escape

from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.common.strings import *
from cs3api4lab.config.config_manager import Cs3ConfigManager
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.exception.exceptions import *
from cs3api4lab.utils.share_utils import ShareUtils

import google.protobuf.field_mask_pb2 as field_masks

class Cs3ShareApi:
    cs3_api = None
    log = None
    auth = None
    config = {}

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)

        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = grpc_gateway.GatewayAPIStub(intercept_channel)
        self.file_api = Cs3FileApi(log)


    def create(self, endpoint, file_path, grantee, idp, role, grantee_type):
        share_permissions = self._get_share_permissions(role)
        grantee_type_enum = self._get_grantee_type(grantee_type)
        share_grant = self._get_share_grant(grantee_type_enum, share_permissions, idp, grantee)
        resource_info = self._get_resource_info(endpoint, file_path)
        create_request = sharing.CreateShareRequest(resource_info=resource_info, grant=share_grant)
        token = self.auth.authenticate()
        create_response = self.cs3_api.CreateShare(request=create_request,
                                                   metadata=[('x-access-token', token)])
        if create_response.status.code == cs3_code.CODE_OK:
            self.log.info("Created share: " + endpoint + file_path + " for " + idp + ":" + grantee)
            self.log.info(create_response)
            return self._map_given_share(create_response.share)
        elif create_response.status.code == cs3_code.CODE_NOT_FOUND:
            self.log.error(f"Resource {file_path} not found")
            raise ResourceNotFoundError(f"Resource {file_path} not found")
        #note the code below doesn't work currently https://github.com/cs3org/reva/issues/2847
        elif create_response.status.code == cs3_code.CODE_ALREADY_EXISTS:
            self.log.error("Share already exists: " + endpoint + file_path + " for " + idp + ":" + grantee)
            raise ShareAlreadyExistsError("Share already exists for file: " + file_path)
        else:
            self._handle_error(create_response)

    def list(self, file_path=None):
        list_request = self._share_filter_by_resource(file_path)
        list_response = self.cs3_api.ListShares(request=list_request,
                                                metadata=[('x-access-token', self.auth.authenticate())])

        if self._is_code_ok(list_response):
            self.log.debug(f"List shares response for user {self.config.client_id}:\n{list_response}")
        else:
            self.log.error("Error listing shares response for user: " + self.config.client_id)
            self._handle_error(list_response)

        return list_response

    def list_shares_for_filepath(self, file_path):
        """
        :param file_path: path to the file
        :return: list of grantees
        """
        share_list = self.list()

        file_path = ShareUtils.purify_file_path(file_path, self.config.client_id)
        shares = []
        for share in share_list.shares:
            path = ShareUtils.purify_file_path(share.resource_id.opaque_id, self.config.client_id)
            if file_path == escape.url_unescape(path):
                shares.append(ShareUtils.get_share_info(share))

        return shares

    def get(self, opaque_id):
        share_id = sharing_res.ShareId(opaque_id=opaque_id)
        ref = sharing_res.ShareReference(id=share_id)
        request = sharing.GetShareRequest(ref=ref)
        share = self.cs3_api.GetShare(request, metadata=[('x-access-token', self.auth.authenticate())])

        if self._is_code_ok(share):
            return share
        else:
            self.log.error(f"Error getting share for opaque_id {opaque_id}")
            raise ShareNotFoundError(f"Error getting share for opaque_id {opaque_id}")

    def remove(self, share_id):
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        remove_request = sharing.RemoveShareRequest(ref=ref)
        remove_response = self.cs3_api.RemoveShare(request=remove_request,
                                                   metadata=[('x-access-token', self.auth.authenticate())])
        if remove_response.status.code == cs3_code.CODE_OK:
            self.log.info("Successfully removed share with ID: " + share_id)
            self.log.info(remove_response)
        elif remove_response.status.code == cs3_code.CODE_NOT_FOUND:
            raise ShareNotFoundError("Error removing share with ID: " + share_id)
        else:
            self._handle_error(remove_response)

    def update(self, share_id, role):
        share_permissions = self._get_share_permissions(role)
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        update_request = sharing.UpdateShareRequest(ref=ref,
                                                    field=sharing.UpdateShareRequest.UpdateField(
                                                        permissions=share_permissions))
        update_response = self.cs3_api.UpdateShare(request=update_request,
                                                   metadata=[('x-access-token', self.auth.authenticate())])
        if update_response.status.code == cs3_code.CODE_OK:
            self.log.info("Successfully updated share: " + share_id + " with role: " + role)
            self.log.info(update_response)
        elif update_response.status.code == cs3_code.CODE_NOT_FOUND:
            raise ShareNotFoundError("Error updating share: " + share_id)
        else:
            self._handle_error(update_response)

    def list_received(self):
        self.log.info("Listing received shares")
        list_request = sharing.ListReceivedSharesRequest()
        list_response = self.cs3_api.ListReceivedShares(request=list_request,
                                                        metadata=[('x-access-token', self.auth.authenticate())])

        if self._is_code_ok(list_response):
            self.log.debug(f"Retrieved received shares for user {self.config.client_id}:\n{list_response}")
            return list_response
        else:
            self.log.error("Error retrieving received shares for user: " + self.config.client_id)
            self._handle_error(list_response)

    def _share_filter_by_resource(self, path):
        if path is None:
            return sharing.ListSharesRequest()

        file_stat = self.file_api.stat_info(path)
        share_filters = []
        resource = storage_resources.ResourceId(
            storage_id=file_stat['inode']['storage_id'],
            opaque_id=file_stat['inode']['opaque_id']
        )
        share_filters.append(sharing_res.Filter(
            resource_id=resource,
            type=sharing_res.Filter.Type.TYPE_RESOURCE_ID
        ))
        list_request = sharing.ListSharesRequest(filters=share_filters)

        return list_request

    def _map_received_shares(self, list_res):
        shares = []
        for share in list_res.shares:
            shares.append({
                "opaque_id": share.share.id.opaque_id,
                "id": {
                    "storage_id": share.share.resource_id.storage_id,
                    "opaque_id": self._purify_file_path(share.share.resource_id.opaque_id),
                },
                "permissions": self._resolve_share_permissions(share.share),
                "grantee": {
                    "type": share.share.grantee.type,
                    "opaque_id": share.share.grantee.user_id.opaque_id,
                    "idp": share.share.grantee.user_id.idp
                },
                "owner": {
                    "idp": share.share.owner.idp,
                    "opaque_id": share.share.owner.opaque_id
                },
                "creator": {
                    "idp": share.share.creator.idp,
                    "opaque_id": share.share.creator.opaque_id
                },
                "state": ShareUtils.map_state(share.state)
            })

        return shares

    def _map_given_share(self, share):
        share_mapped = {
            "opaque_id": share.id.opaque_id,
            "id": {
                "storage_id": share.resource_id.storage_id,
                "opaque_id": ShareUtils.purify_file_path(share.resource_id.opaque_id, self.config.client_id),
            },
            "permissions": self._resolve_share_permissions(share),
            "grantee": {
                "type": self._map_grantee(share),
                "opaque_id": share.grantee.user_id.opaque_id,
                "idp": share.grantee.user_id.idp
            },
            "owner": {
                "idp": share.owner.idp,
                "opaque_id": share.owner.opaque_id
            },
            "creator": {
                "idp": share.creator.idp,
                "opaque_id": share.creator.opaque_id
            }
        }
        return share_mapped

    def _map_given_shares(self, list_res):
        shares = []
        for share in list_res.shares:
            shares.append(self._map_given_share(share))
        return shares

    def _map_grantee(self, share):
        if share.grantee.type == storage_resources.GranteeType.GRANTEE_TYPE_USER:
            return Grantee.USER
        if share.grantee.type == storage_resources.GranteeType.GRANTEE_TYPE_GROUP:
            return Grantee.GROUP

    def update_received(self, share_id, state=State.ACCEPTED):
        share_state = ShareUtils.map_state(state)
        list_request = sharing.ListReceivedSharesRequest()
        list_response = self.cs3_api.ListReceivedShares(request=list_request,
                                                        metadata=[('x-access-token', self.auth.authenticate())])
        share_to_update = None
        for share in list_response.shares:
            if share_id == share.share.id.opaque_id:
                share_to_update = share
        if not share_to_update:
            raise ShareNotFoundError(f"Received share {share_id} not found")

        update_request = sharing.UpdateReceivedShareRequest(
            share=sharing_res.ReceivedShare(
                share=share_to_update.share,
                state=share_state,
                mount_point=FileUtils.get_reference(share_to_update.share.resource_id.opaque_id,
                                                    share_to_update.share.resource_id.storage_id)),
            update_mask=field_masks.FieldMask(paths=["state"])
        )

        update_response = self.cs3_api.UpdateReceivedShare(request=update_request,
                                                           metadata=[('x-access-token', self.auth.authenticate())])
        if self._is_code_ok(update_response):
            self.log.info("Successfully updated share: " + share_id + " with state " + state)
            self.log.info(update_response)
        else:
            self.log.error("Error updating received share: " + share_id + " with state " + state)
            self._handle_error(update_response)
        return update_response.share

    def _resolve_share_permissions(self, share):
        has_move_permission = share.permissions.permissions.move is True
        has_delete_permission = share.permissions.permissions.delete is True
        if has_move_permission and has_delete_permission:
            return Role.EDITOR
        else:
            return Role.VIEWER

    def _get_resource_info(self, endpoint, file_id):
        ref = FileUtils.get_reference(file_id, endpoint)
        stat_response = self.cs3_api.Stat(request=storage_provider.StatRequest(ref=ref),
                                          metadata=[('x-access-token', self.auth.authenticate())])
        if stat_response.status.code == cs3_code.CODE_OK:
            return stat_response.info
        elif stat_response.status.code == cs3_code.CODE_NOT_FOUND:
            raise ResourceNotFoundError("Resource not found")
        else:
            self._handle_error(stat_response)

    def _get_share_grant(self, grantee_type, share_permissions, idp, grantee):
        user_id = identity_res.UserId(idp=idp, opaque_id=grantee)
        resources_grantee = storage_resources.Grantee(user_id=user_id, type=grantee_type)
        return sharing_res.ShareGrant(permissions=share_permissions, grantee=resources_grantee)

    def _get_grantee_type(self, grantee_type):
        if grantee_type == Grantee.USER:
            return storage_resources.GranteeType.GRANTEE_TYPE_USER
        if grantee_type == Grantee.GROUP:
            return storage_resources.GranteeType.GRANTEE_TYPE_GROUP
        raise InvalidTypeError("Invalid grantee type")

    def _get_share_permissions(self, role):
        if role == Role.VIEWER:
            permissions = storage_resources.ResourcePermissions(get_path=True,
                                                                get_quota=True,
                                                                initiate_file_download=True,
                                                                list_file_versions=True,
                                                                list_container=True,
                                                                list_grants=True,
                                                                list_recycle=True,
                                                                stat=True)
            return sharing_res.SharePermissions(permissions=permissions)
        if role == Role.EDITOR:
            permissions = storage_resources.ResourcePermissions(get_path=True,
                                                                initiate_file_download=True,
                                                                list_file_versions=True,
                                                                list_container=True,
                                                                stat=True,
                                                                create_container=True,
                                                                delete=True,
                                                                initiate_file_upload=True,
                                                                restore_file_version=True,
                                                                move=True)
            return sharing_res.SharePermissions(permissions=permissions)
        else:
            raise InvalidTypeError("Invalid role")

    def _is_code_ok(self, response):
        return response.status.code == cs3_code.CODE_OK

    def _handle_error(self, response):
        self.log.error(response)
        raise ShareError("Incorrect server response: " + response.status.message)
