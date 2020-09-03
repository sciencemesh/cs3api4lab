"""
cs3_share_api.py

CS3 Share API for the JupyterLab Extension

Authors:
"""

import re
import time
import grpc
import logging
import cs3.gateway.v1beta1.gateway_api_pb2 as gateway
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway
import cs3.sharing.collaboration.v1beta1.collaboration_api_pb2 as sharing
import cs3.sharing.collaboration.v1beta1.resources_pb2 as sharing_res
import cs3.storage.provider.v1beta1.provider_api_pb2 as storage_provider
import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
import cs3.identity.user.v1beta1.resources_pb2 as identity_res
import cs3.rpc.v1beta1.code_pb2 as cs3_code
import random

class Cs3ShareApi:
    tokens = {}
    gateway_stub = None
    log = None
    config = {
        "revahost": "127.0.0.1:19000",
        "authtokenvalidity": 3600,
        "userid": "einstein",
        "endpoint": "/",
        "chunksize": 4194304
    }

    def __init__(self):
        channel = grpc.insecure_channel(self.config["revahost"])
        self.gateway_stub = grpc_gateway.GatewayAPIStub(channel)

        log = logging.getLogger("CS3_SHARE_API_LOG")
        log.setLevel(level=logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level=logging.DEBUG)
        log.addHandler(console_handler)
        self.log = log
        return

    def create(self, endpoint, fileid, grantee, idp=None, role="viewer", grantee_type="user"):
        if grantee is None:
            raise Exception("Grantee was not provided")
        share_permissions = self._get_share_permissions(role)
        grantee_type_enum = self._get_grantee_type(grantee_type)
        share_grant = self._get_share_grant(grantee_type_enum, share_permissions, idp, grantee)
        resource_info = self._get_resource_info(endpoint, fileid)
        share_request = sharing.CreateShareRequest(resource_info=resource_info, grant=share_grant)
        token = self._get_token()
        share_response = self.gateway_stub.CreateShare(request=share_request,
                                                       metadata=[('x-access-token', token)])
        self._check_response_code(share_response)
        self.log.info("Share created")
        self.log.info(share_response)
        return self._map_given_share(share_response.share)

    def list(self):
        # todo filters
        list_request = sharing.ListSharesRequest()
        list_response = self.gateway_stub.ListShares(request=list_request,
                                                     metadata=[('x-access-token', self._get_token())])
        self._check_response_code(list_response)
        self.log.info("List shares response for user: einstein")
        self.log.info(list_request)
        return self._map_given_shares(list_response)

    def list_grantees_for_file(self, file_id):
        shares_response = self.list()

        shares = []
        for share in shares_response:
            # todo regex
            if file_id == self._decode_file_id(share['id']['opaque_id']):
                shares.append(share)

        shares_dict = {}
        for share in shares:
            # permissions = self._resolveSharePermissions(share)
            opaque_id = share['grantee']['opaque_id']
            shares_dict[opaque_id] = share['permissions']

        return shares_dict

    def _map_opaque_id(self, opaque_id):
        # todo implement
        return "user" + str(random.randint(0, 10))

    def _decode_file_id(self, file_id):
        if '%2F' in file_id:
            return re.search('(?=%2F).*', file_id).group(0).replace('%2F', '/')
        else:
            return file_id

    def remove(self, share_id):
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        remove_request = sharing.RemoveShareRequest(ref=ref)
        remove_response = self.gateway_stub.RemoveShare(request=remove_request,
                                                        metadata=[('x-access-token', self._get_token())])
        self._check_response_code(remove_response)
        self.log.info("Removing share " + share_id)
        return

    def update(self, share_id, role):
        # todo check role
        share_permissions = self._get_share_permissions(role)
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        update_request = sharing.UpdateShareRequest(ref=ref,
                                                    field=sharing.UpdateShareRequest.UpdateField(
                                                        permissions=share_permissions))
        update_response = self.gateway_stub.UpdateShare(request=update_request,
                                                        metadata=[('x-access-token', self._get_token())])
        self._check_response_code(update_response)
        return

    def list_received(self):
        list_request = sharing.ListReceivedSharesRequest()
        list_response = self.gateway_stub.ListReceivedShares(request=list_request,
                                                             metadata=[('x-access-token', self._get_token())])
        self._check_response_code(list_response)
        self.log.info("List received shares response for user: " + 'einstein')
        self.log.info(list_response)
        return self._map_received_shares(list_response)

    def _map_received_shares(self, list_res):
        shares = []
        for share in list_res.shares:
            shares.append({
                "opaque_id": share.share.id.opaque_id,
                "id": {
                    "storage_id": share.share.resource_id.storage_id,
                    "opaque_id": self._decode_file_id(share.share.resource_id.opaque_id),
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
                "opaque_id": self._decode_file_id(share.resource_id.opaque_id),
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
            },
            # "state": share.state
        }
        return share_mapped

    def _map_given_shares(self, list_res):
        shares = []
        for share in list_res.shares:
            shares.append(self._map_given_share(share))
        return shares

    def _map_grantee(self, share):
        if share.grantee.type == storage_resources.GranteeType.GRANTEE_TYPE_USER:
            return 'user'
        if share.grantee.type == storage_resources.GranteeType.GRANTEE_TYPE_GROUP:
            return 'group'

    def update_received(self, share_id, state="pending"):
        # todo validate flags + tuple
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        share_state = self._map_share_state(state)
        update_request = sharing.UpdateReceivedShareRequest(ref=ref,
                                                            field=sharing.UpdateReceivedShareRequest.UpdateField(
                                                                state=share_state))
        update_response = self.gateway_stub.UpdateReceivedShare(request=update_request,
                                                                metadata=[('x-access-token', self._get_token())])
        self._check_response_code(update_response)
        return

    def _resolve_share_permissions(self, share):
        has_move_permission = share.permissions.permissions.move is True
        has_delete_permission = share.permissions.permissions.delete is True
        if has_move_permission and has_delete_permission:
            return "editor"
        else:
            return "viewer"

    def _get_token(self):
        # todo export
        user_id = "einstein"
        auth_req = gateway.AuthenticateRequest(type='basic', client_id='einstein', client_secret='relativity')
        if user_id not in self.tokens or self.tokens[user_id]['exp'] < time.time():
            auth_res = self.gateway_stub.Authenticate(auth_req)
            self.tokens[user_id] = {'token': auth_res.token, 'exp': time.time() + self.config['authtokenvalidity']}
        # return self.gateway_stub.Authenticate(auth_req).token
        return self.tokens[user_id]['token']

    def _get_resource_info(self, endpoint, file_id):
        ref = self._get_reference(endpoint, file_id)
        token = self._get_token()
        stat_info = self.gateway_stub.Stat(request=storage_provider.StatRequest(ref=ref),
                                           metadata=[('x-access-token', token)])
        return stat_info.info

    def _get_share_grant(self, grantee_type, share_permissions, idp, grantee):
        user_id = identity_res.UserId(idp=idp, opaque_id=grantee)
        resources_grantee = storage_resources.Grantee(id=user_id, type=grantee_type)
        return sharing_res.ShareGrant(permissions=share_permissions, grantee=resources_grantee)

    def _get_grantee_type(self, grantee_type):
        if grantee_type == "user":
            return storage_resources.GranteeType.GRANTEE_TYPE_USER
        if grantee_type == "group":
            return storage_resources.GranteeType.GRANTEE_TYPE_GROUP
        raise Exception("Invalid grantee type")

    def _get_share_permissions(self, role):
        if role == "viewer":
            permissions = storage_resources.ResourcePermissions(get_path=True,
                                                                initiate_file_download=True,
                                                                list_file_versions=True,
                                                                list_container=True,
                                                                stat=True)
            return sharing_res.SharePermissions(permissions=permissions)
        if role == "editor":
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
            if state == "pending":
                return sharing_res.SHARE_STATE_PENDING
            elif state == "accepted":
                return sharing_res.SHARE_STATE_ACCEPTED
            elif state == "rejected":
                return sharing_res.SHARE_STATE_REJECTED
            elif state == "invalid":
                return sharing_res.SHARE_STATE_INVALID
        else:
            if state == sharing_res.SHARE_STATE_PENDING:
                return "pending"
            elif state == sharing_res.SHARE_STATE_ACCEPTED:
                return "accepted"
            elif state == sharing_res.SHARE_STATE_REJECTED:
                return "rejected"
            elif state == sharing_res.SHARE_STATE_INVALID:
                return "invalid"

        raise Exception("Unknown share state")

    def _get_reference(self, endpoint, fileid):
        if endpoint == 'default':
            raise IOError('A CS3API-compatible storage endpoint must be identified by a storage UUID')
        if fileid[0] == '/':
            # assume this is a filepath
            ref = storage_resources.Reference(path=fileid)
        else:
            # assume we have an opaque fileid
            ref = storage_resources.Reference(id=storage_resources.ResourceId(storage_id=endpoint,
                                                                              opaque_id=fileid))
        return ref

    def _check_response_code(self, response):
        if response.status.code != cs3_code.CODE_OK:
            self.log.error("Server response is not OK: ")
            self.log.error(response)
            raise Exception("Incorrect server response: " + response.status.message)