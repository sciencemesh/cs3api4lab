"""
cs3_share_api.py

CS3 Share API for the JupyterLab Extension

Authors:
"""

import urllib.parse
import cs3.sharing.collaboration.v1beta1.collaboration_api_pb2 as sharing
import cs3.sharing.collaboration.v1beta1.resources_pb2 as sharing_res
import cs3.storage.provider.v1beta1.provider_api_pb2 as storage_provider
import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
import cs3.identity.user.v1beta1.resources_pb2 as identity_res
import cs3.rpc.v1beta1.code_pb2 as cs3_code
from cs3api4lab.auth.authenticator import Authenticator
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.file_utils import FileUtils
from cs3api4lab.common.strings import *
from cs3api4lab.config.config_manager import Cs3ConfigManager
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway
from cs3api4lab.auth.channel_connector import ChannelConnector


class Cs3ShareApi:
    gateway_stub = None
    log = None
    auth = None
    config = {}
    file_api = None

    def __init__(self, log):
        self.config = Cs3ConfigManager().config
        self.auth = Authenticator()
        self.file_api = Cs3FileApi(log)
        self.gateway_stub = grpc_gateway.GatewayAPIStub(ChannelConnector().channel)
        self.log = log
        return

    def create(self, endpoint, file_path, grantee, idp, role=Role.VIEWER, grantee_type=Grantee.USER):
        if grantee is None:
            raise Exception("Grantee was not provided")
        share_permissions = self._get_share_permissions(role)
        grantee_type_enum = self._get_grantee_type(grantee_type)
        share_grant = self._get_share_grant(grantee_type_enum, share_permissions, idp, grantee)
        resource_info = self._get_resource_info(endpoint, file_path)
        share_request = sharing.CreateShareRequest(resource_info=resource_info, grant=share_grant)
        token = self.get_token()
        share_response = self.gateway_stub.CreateShare(request=share_request,
                                                       metadata=[('x-access-token', token)])
        self._check_response_code(share_response)
        self.log.info("Share created")
        self.log.info(share_response)
        return self._map_given_share(share_response.share)

    def list(self):
        list_request = sharing.ListSharesRequest()
        list_response = self.gateway_stub.ListShares(request=list_request,
                                                     metadata=[('x-access-token', self.get_token())])
        self._check_response_code(list_response)
        self.log.info("List shares response for user: " + self.config['client_id'])
        self.log.info(list_request)
        return self._map_given_shares(list_response)

    def list_grantees_for_file(self, storage_id, file_path):
        file_path = urllib.parse.quote('fileid-' + self.config['client_id'] + file_path, safe='')
        resource_id = storage_resources.ResourceId(storage_id=storage_id, opaque_id=file_path)
        resource_filter = sharing.ListSharesRequest.Filter(
            resource_id=resource_id,
            type=sharing.ListSharesRequest.Filter.Type.TYPE_RESOURCE_ID)
        list_request = sharing.ListSharesRequest(filters=[resource_filter])
        shares_response = self.gateway_stub.ListShares(request=list_request,
                                                       metadata=[('x-access-token', self.get_token())])

        shares_dict = {}
        for share in shares_response.shares:
            opaque_id = share.grantee.id.opaque_id
            shares_dict[opaque_id] = self._resolve_share_permissions(share)

        return shares_dict

    def _decode_file_path(self, file_path):
        return urllib.parse.unquote(file_path)

    def _purify_file_path(self, file_path):
        return self._decode_file_path(file_path.replace('fileid-' + self.config['client_id'], ''))

    def remove(self, share_id):
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        remove_request = sharing.RemoveShareRequest(ref=ref)
        remove_response = self.gateway_stub.RemoveShare(request=remove_request,
                                                        metadata=[('x-access-token', self.get_token())])
        self._check_response_code(remove_response)
        self.log.info("Removing share " + share_id)
        return

    def update(self, share_id, role):
        share_permissions = self._get_share_permissions(role)
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        update_request = sharing.UpdateShareRequest(ref=ref,
                                                    field=sharing.UpdateShareRequest.UpdateField(
                                                        permissions=share_permissions))
        update_response = self.gateway_stub.UpdateShare(request=update_request,
                                                        metadata=[('x-access-token', self.get_token())])
        self._check_response_code(update_response)
        return

    def list_received(self):
        list_request = sharing.ListReceivedSharesRequest()
        list_response = self.gateway_stub.ListReceivedShares(request=list_request,
                                                             metadata=[('x-access-token', self.get_token())])
        self._check_response_code(list_response)
        self.log.info("List received shares response for user: " + self.config['client_id'])
        self.log.info(list_response)
        return self._map_received_shares(list_response)

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
                    "opaque_id": share.share.grantee.id.opaque_id,
                    "idp": share.share.grantee.id.idp
                },
                "owner": {
                    "idp": share.share.owner.idp,
                    "opaque_id": share.share.owner.opaque_id
                },
                "creator": {
                    "idp": share.share.creator.idp,
                    "opaque_id": share.share.creator.opaque_id
                },
                "state": self._map_share_state(share.state)
            })

        return shares

    def _map_given_share(self, share):
        share_mapped = {
            "opaque_id": share.id.opaque_id,
            "id": {
                "storage_id": share.resource_id.storage_id,
                "opaque_id": self._purify_file_path(share.resource_id.opaque_id),
            },
            "permissions": self._resolve_share_permissions(share),
            "grantee": {
                "type": self._map_grantee(share),
                "opaque_id": share.grantee.id.opaque_id,
                "idp": share.grantee.id.idp
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

    def update_received(self, share_id, state=State.PENDING):
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        share_state = self._map_share_state(state)
        update_request = sharing.UpdateReceivedShareRequest(ref=ref,
                                                            field=sharing.UpdateReceivedShareRequest.UpdateField(
                                                                state=share_state))
        update_response = self.gateway_stub.UpdateReceivedShare(request=update_request,
                                                                metadata=[('x-access-token', self.get_token())])
        self._check_response_code(update_response)
        return

    def _resolve_share_permissions(self, share):
        has_move_permission = share.permissions.permissions.move is True
        has_delete_permission = share.permissions.permissions.delete is True
        if has_move_permission and has_delete_permission:
            return Role.EDITOR
        else:
            return Role.VIEWER

    def _get_resource_info(self, endpoint, file_id):
        ref = FileUtils.get_reference(file_id, self.config['home_dir'], endpoint)
        token = self.get_token()
        stat_info = self.gateway_stub.Stat(request=storage_provider.StatRequest(ref=ref),
                                           metadata=[('x-access-token', token)])
        return stat_info.info

    def _get_share_grant(self, grantee_type, share_permissions, idp, grantee):
        user_id = identity_res.UserId(idp=idp, opaque_id=grantee)
        resources_grantee = storage_resources.Grantee(id=user_id, type=grantee_type)
        return sharing_res.ShareGrant(permissions=share_permissions, grantee=resources_grantee)

    def _get_grantee_type(self, grantee_type):
        if grantee_type == Grantee.USER:
            return storage_resources.GranteeType.GRANTEE_TYPE_USER
        if grantee_type == Grantee.GROUP:
            return storage_resources.GranteeType.GRANTEE_TYPE_GROUP
        raise Exception("Invalid grantee type")

    def _get_share_permissions(self, role):
        if role == Role.VIEWER:
            permissions = storage_resources.ResourcePermissions(get_path=True,
                                                                initiate_file_download=True,
                                                                list_file_versions=True,
                                                                list_container=True,
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
            raise Exception("Invalid role")

    def _map_share_state(self, state):
        if isinstance(state, str):
            if state == State.PENDING:
                return sharing_res.SHARE_STATE_PENDING
            elif state == State.ACCEPTED:
                return sharing_res.SHARE_STATE_ACCEPTED
            elif state == State.REJECTED:
                return sharing_res.SHARE_STATE_REJECTED
            elif state == State.INVALID:
                return sharing_res.SHARE_STATE_INVALID
        else:
            if state == sharing_res.SHARE_STATE_PENDING:
                return State.ACCEPTED
            elif state == sharing_res.SHARE_STATE_ACCEPTED:
                return State.ACCEPTED
            elif state == sharing_res.SHARE_STATE_REJECTED:
                return State.REJECTED
            elif state == sharing_res.SHARE_STATE_INVALID:
                return State.INVALID

        raise Exception("Unknown share state")

    def _check_response_code(self, response):
        if response.status.code != cs3_code.CODE_OK:
            self.log.error("Server response is not OK: ")
            self.log.error(response)
            raise Exception("Incorrect server response: " + response.status.message)

    def get_token(self):
        return self.auth.authenticate(self.config['client_id'])
