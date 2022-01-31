"""
cs3_public_share_api.py

CS3 OCM Shares API for the JupyterLab Extension

"""
import cs3.sharing.ocm.v1beta1.resources_pb2 as sharing_res
import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
import cs3.sharing.link.v1beta1.link_api_pb2_grpc as link_api_grpc
import cs3.ocm.provider.v1beta1.provider_api_pb2 as ocm_provider_api
import cs3.ocm.provider.v1beta1.provider_api_pb2_grpc as ocm_provider_api_grpc
import grpc

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.config.config_manager import Cs3ConfigManager
from cs3api4lab.auth.channel_connector import ChannelConnector

import cs3.sharing.ocm.v1beta1.ocm_api_pb2 as ocm_api
import cs3.sharing.ocm.v1beta1.ocm_api_pb2_grpc as ocm_api_grpc
import cs3.identity.user.v1beta1.resources_pb2 as identity_res
import cs3.types.v1beta1.types_pb2 as cs3_types
import cs3.rpc.v1beta1.code_pb2 as cs3_code
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway

from cs3api4lab.utils.share_utils import ShareUtils
from cs3api4lab.common.strings import *
from cs3.storage.provider.v1beta1.resources_pb2 import *


class Cs3OcmShareApi:

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        self.file_api = Cs3FileApi(log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = grpc_gateway.GatewayAPIStub(intercept_channel)
        self.public_share_api = link_api_grpc.LinkAPIStub(channel)
        self.ocm_share_api = ocm_api_grpc.OcmAPIStub(channel)
        self.provider_api = ocm_provider_api_grpc.ProviderAPIStub(channel)
        return

    def create(self, opaque_id, idp, domain, endpoint, file_path, grantee_type=GRANTEE_TYPE_USER, role=Role.EDITOR, reshare=True):
        opaque = cs3_types.Opaque(
            map={"permissions": cs3_types.OpaqueEntry(decoder="plain",
                                                      value=str.encode(self._map_role(role))),
                 "name": cs3_types.OpaqueEntry(decoder="plain",
                                               value=str.encode('my_resource_name'))})
        resource_id = storage_resources.ResourceId(storage_id=endpoint, opaque_id=file_path)
        user_id = identity_res.UserId(idp=idp, opaque_id=opaque_id)
        opaque_id = storage_resources.Grantee(type=ShareUtils.map_grantee(grantee_type), user_id=user_id)
        perms = sharing_res.SharePermissions(permissions=ShareUtils.get_resource_permissions(role),
                                             reshare=bool(reshare))
        grant = sharing_res.ShareGrant(permissions=perms, grantee=opaque_id)
        provider_info = self._get_provider_info(domain)
        request = ocm_api.CreateOCMShareRequest(opaque=opaque,
                                                resource_id=resource_id,
                                                grant=grant,
                                                recipient_mesh_provider=provider_info)
        response = self.ocm_share_api.CreateOCMShare(request=request,
                                                     metadata=self._token())
        if self._is_code_ok(response):
            self.log.info("OCM share created:\n")
        else:
            self._handle_error(response, "Error creating OCM share")
        return self._map_share(response.share)

    def remove(self, share_id):
        share_id_obj = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_obj)
        request = ocm_api.RemoveOCMShareRequest(ref=ref)
        response = self.ocm_share_api.RemoveOCMShare(request=request,
                                                     metadata=self._token())
        if self._is_code_ok(response):
            self.log.info("OCM share deleted: " + share_id)
            return
        else:
            self._handle_error(response, "Error removing OCM share")

    def update(self, share_id, field, value):
        share_id_obj = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_obj)
        if field == 'permissions':
            request = ocm_api.UpdateOCMShareRequest(ref=ref,
                                                    field=ocm_api.UpdateOCMShareRequest.UpdateField(
                                                        permissions=sharing_res.SharePermissions(
                                                            permissions=ShareUtils.get_resource_permissions(value[0]),
                                                            reshare=bool(value[1]))
                                                    ))
        elif field == 'display_name':
            request = ocm_api.UpdateOCMShareRequest(ref=ref,
                                                    field=ocm_api.UpdateOCMShareRequest.UpdateField(
                                                        display_name=value
                                                    ))
        else:
            raise ValueError('Unknown field to update')

        response = self.ocm_share_api.UpdateOCMShare(request=request,
                                                     metadata=self._token())
        if self._is_code_ok(response):
            self.log.info("OCM share updated:\n" + share_id)
            return
        else:
            self._handle_error(response, "Error updating OCM share:")

    def update_received(self, ocm_share_id, field, value):
        share_id_obj = sharing_res.ShareId(opaque_id=ocm_share_id)
        ref = sharing_res.ShareReference(id=share_id_obj)
        if field == 'display_name':
            request = ocm_api.UpdateReceivedOCMShareRequest(ref=ref,
                                                            field=ocm_api.UpdateReceivedOCMShareRequest
                                                            .UpdateField(
                                                                display_name=value
                                                            ))
        elif field == 'state':
            request = ocm_api.UpdateReceivedOCMShareRequest(ref=ref,
                                                            field=ocm_api.UpdateReceivedOCMShareRequest
                                                            .UpdateField(
                                                                state=ShareUtils.map_state(value)
                                                            ))
        else:
            raise ValueError("Unknown field to update")

        response = self.ocm_share_api.UpdateReceivedOCMShare(request=request,
                                                             metadata=self._token())
        if self._is_code_ok(response):
            self.log.info("OCM received share updated: " + ocm_share_id)
            return
        else:
            self._handle_error(response, "Error updating OCM received share:")
        return response

    def list(self, share_id=None):
        if share_id is None:
            return self._list_ocm_shares()
        else:
            return self._get_ocm_share(share_id)

    def _list_ocm_shares(self):
        request = ocm_api.ListOCMSharesRequest()
        response = self.ocm_share_api.ListOCMShares(request=request,
                                                    metadata=self._token())
        if not self._is_code_ok(response):
            self._handle_error(response, "Error listing OCM share:")
        return response

    def _get_ocm_share(self, share_id):
        share_id_obj = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_obj)
        request = ocm_api.GetOCMShareRequest(ref=ref)
        response = self.ocm_share_api.GetOCMShare(request=request, metadata=self._token())
        return self._map_share(response.share)

    def get_received_ocm_shares(self, share_id):
        if share_id is None:
            return self.list_received()
        else:
            return self._get_received_share(share_id)

    def list_received(self):
        request = ocm_api.ListReceivedOCMSharesRequest()
        response = self.ocm_share_api.ListReceivedOCMShares(request=request,
                                                            metadata=self._token())
        if not self._is_code_ok(response):
            self._handle_error(response, "Error listing OCM received shares: ")
        return response

    def get_received_share(self, share_id):
        share_id_obj = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_obj)
        request = ocm_api.GetReceivedOCMShareRequest(ref=ref)
        response = self.ocm_share_api.GetReceivedOCMShare(request=request,
                                                          metadata=self._token())
        return self._map_share(response.share.share, response.share.state)

    def _map_ocm_shares(self, list_response, received=False):
        shares = []
        if received:
            for share in list_response.shares:
                shares.append(self._map_share(share.share, share.state))
        else:
            for share in list_response.shares:
                shares.append(self._map_share(share))
        return shares

    def _map_share(self, share, state=None):
        response = {
            "id": share.id.opaque_id,
            "storage_id": share.resource_id.storage_id,
            "opaque_id": share.resource_id.opaque_id,
            "name": share.name,
            "permissions": ShareUtils.map_permissions_to_role(share.permissions.permissions),
            "grantee": {
                "type": ShareUtils.map_grantee_type(share),
                "idp": share.grantee.user_id.idp,
                "opaque_id": share.grantee.user_id.opaque_id
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
        if state:
            response.update({"state": ShareUtils.map_state(state)})

        return response

    def _get_provider_info(self, domain):
        request = ocm_provider_api.GetInfoByDomainRequest(domain=domain)
        response = self.provider_api.GetInfoByDomain(request=request,
                                                     metadata=self._token())
        return response.provider_info

    def _map_role(self, role):
        if role == Role.VIEWER:
            return '1'
        if role == Role.EDITOR:
            return '15'

    def _is_code_ok(self, response):
        return response.status.code == cs3_code.CODE_OK

    def _handle_error(self, response, msg=''):
        self.log.error(msg + '\n' + response.status.message)
        raise Exception("Incorrect server response: " + response.status.message)

    def _token(self):
        return [('x-access-token', self.auth.authenticate())]
