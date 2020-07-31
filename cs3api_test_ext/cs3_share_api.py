"""
cs3_share_api.py

CS3 Share API for the JupyterLab Extension

Authors:
"""

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


# todo refactor
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
        share_permissions = self._getSharePermissions(role)
        grantee_type_enum = self._getGranteeType(grantee_type)
        share_grant = self._getShareGrant(grantee_type_enum, share_permissions, idp, grantee)
        resource_info = self._getResourceInfo(endpoint, fileid)
        share_request = sharing.CreateShareRequest(resource_info=resource_info, grant=share_grant)
        token = self._getToken()
        share_response = self.gateway_stub.CreateShare(request=share_request,
                                                       metadata=[('x-access-token', token)])
        self.log.info("Share created")
        self.log.info(share_response)
        return self._map_given_shares()

    def list(self):
        # todo filters
        list_req = sharing.ListSharesRequest()
        list_res = self.gateway_stub.ListShares(request=list_req,
                                                metadata=[('x-access-token', self._getToken())])
        self.log.info("List shares response for user: einstein")
        self.log.info(list_req)
        return self._map_given_shares(list_res)

    def list_grantees_for_file(self, file_id):
        list_res = self.list("einstein")

        shares = []
        for share in list_res.shares:
            # todo regex
            if file_id == share.resource_id.opaque_id.replace("fileid-einstein", "").replace('%2F', '/'):
                shares.append(share)

        shares_dict = {}
        for share in shares:
            permissions = self._resolveSharePermissions(share)
            grantee_username = share.grantee.id.opaque_id
            shares_dict[grantee_username] = permissions

        return shares_dict

    def remove(self, shareid):
        share_id_object = sharing_res.ShareId(opaque_id=shareid)
        ref = sharing_res.ShareReference(id=share_id_object)
        remove_req = sharing.RemoveShareRequest(ref=ref)
        remove_res = self.gateway_stub.RemoveShare(request=remove_req,
                                                   metadata=[('x-access-token', self._getToken())])
        self.log.info("Removing share " + shareid)
        return remove_res

    def update(self, endpoint, shareid, userid, role="viewer"):
        # todo check role
        share_permissions = self._getSharePermissions(role)
        share_id_object = sharing_res.ShareId(opaque_id=shareid)
        ref = sharing_res.ShareReference(id=share_id_object)
        update_req = sharing.UpdateShareRequest(ref=ref,
                                                field=sharing.UpdateShareRequest.UpdateField(
                                                    permissions=share_permissions))
        update_res = self.gateway_stub.UpdateShare(request=update_req,
                                                   metadata=[('x-access-token', self._getToken())])
        return update_res

    def list_received(self):
        list_req = sharing.ListReceivedSharesRequest()
        list_res = self.gateway_stub.ListReceivedShares(request=list_req,
                                                        metadata=[('x-access-token', self._getToken())])
        self.log.info("List received shares response for user: " + 'einstein')
        self.log.info(list_res)
        return self._map_received_shares(list_res)

    def _map_received_shares(self, list_res):
        shares = []
        for share in list_res.shares:
            shares.append({
                "opaque_id": share.share.id.opaque_id,
                "id": {
                    "storage_id": share.share.resource_id.storage_id,
                    "opaque_id": share.share.resource_id.opaque_id,
                },
                "permissions": self._resolveSharePermissions(share.share),
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
                "state": share.state
            })

        return shares

    def _map_given_shares(self, list_res):
        shares = []
        for share in list_res.shares:
            shares.append({
                "opaque_id": share.id.opaque_id,
                "id": {
                    "storage_id": share.resource_id.storage_id,
                    "opaque_id": share.resource_id.opaque_id,
                },
                "permissions": self._resolveSharePermissions(share),
                "grantee": {
                    "type": share.grantee.type,
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
            })

        return shares

    def update_received(self, endpoint, shareid, userid, state="pending"):
        # todo validate flags + tuple
        share_id_object = sharing_res.ShareId(opaque_id=shareid)
        ref = sharing_res.ShareReference(id=share_id_object)
        share_state = self._getShareState(state)
        update_req = sharing.UpdateReceivedShareRequest(ref=ref,
                                                        field=sharing.UpdateReceivedShareRequest.UpdateField(
                                                            state=share_state))
        update_res = self.gateway_stub.UpdateReceivedShare(request=update_req,
                                                           metadata=[('x-access-token', self._getToken())])
        return update_res

    def _resolveSharePermissions(self, share):
        return "editor" if share.permissions.permissions.delete is True \
                           and share.permissions.permissions.move is True else "viewer"

    def _getToken(self):
        # todo export
        userid = "einstein"
        auth_req = gateway.AuthenticateRequest(type='basic', client_id='einstein', client_secret='relativity')
        if userid not in self.tokens or self.tokens[userid]['exp'] < time.time():
            auth_res = self.gateway_stub.Authenticate(auth_req)
            self.tokens[userid] = {'token': auth_res.token, 'exp': time.time() + self.config['authtokenvalidity']}
        # return self.gateway_stub.Authenticate(auth_req).token
        return self.tokens[userid]['token']

    def _getResourceInfo(self, endpoint, fileid):
        ref = self._getReference(endpoint, fileid)
        token = self._getToken()
        stat_info = self.gateway_stub.Stat(request=storage_provider.StatRequest(ref=ref),
                                           metadata=[('x-access-token', token)])
        return stat_info.info

    def _getShareGrant(self, grantee_type, share_permissions, idp, grantee):
        user_id = identity_res.UserId(idp=idp, opaque_id=grantee)
        resources_grantee = storage_resources.Grantee(id=user_id, type=grantee_type)
        return sharing_res.ShareGrant(permissions=share_permissions, grantee=resources_grantee)

    def _getGranteeType(self, grantee_type):
        if grantee_type == "user":
            return storage_resources.GranteeType.GRANTEE_TYPE_USER
        if grantee_type == "group":
            return storage_resources.GranteeType.GRANTEE_TYPE_GROUP
        raise Exception("Invalid grantee type")

    def _getSharePermissions(self, role):
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

    def _getShareState(self, state):
        if state == "pending":
            return sharing_res.SHARE_STATE_PENDING
        elif state == "accepted":
            return sharing_res.SHARE_STATE_ACCEPTED
        elif state == "rejected":
            return sharing_res.SHARE_STATE_REJECTED
        elif state == "invalid":
            return sharing_res.SHARE_STATE_INVALID
        else:
            raise Exception("Unknown share state")

    def _getReference(self, endpoint, fileid):
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
