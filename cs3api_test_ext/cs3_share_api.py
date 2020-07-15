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
import cs3.sharing.collaboration.v1beta1.collaboration_api_pb2_grpc as sharing_grpc
import cs3.storage.provider.v1beta1.provider_api_pb2 as storage_provider
import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
import cs3.identity.user.v1beta1.resources_pb2 as identity_res
import cs3.identity.user.v1beta1.resources_pb2_grpc as identity_res_grpc

from cs3api_test_ext.cs3_file_api import Cs3FileApi


class Cs3ShareApi:
    gateway_stub = None
    config = {
        "revahost": "127.0.0.1:19000",
        "authtokenvalidity": 3600,
        "userid": "einstein",
        "endpoint": "/",
        "chunksize": 4194304
    }
    log = None

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

    def create(self, endpoint, fileid, userid, grantee, idp=None, role="viewer", grantee_type="user"):
        if grantee is None:
            raise Exception("Grantee was not provided")
        share_permissions = self._getSharePermissions(role)
        grantee_type_enum = self._getGranteeType(grantee_type)
        share_grant = self._getShareGrant(grantee_type_enum, share_permissions, idp, grantee)
        resource_info = self._getResourceInfo(endpoint, fileid, userid)
        share_request = sharing.CreateShareRequest(resource_info=resource_info, grant=share_grant)
        token = self._getToken(userid)
        share_response = self.gateway_stub.CreateShare(request=share_request,
                                                       metadata=[('x-access-token', token)])
        self.log.info(share_response)
        return

    def _getToken(self, userid):
        auth_req = gateway.AuthenticateRequest(type='basic', client_id='einstein', client_secret='relativity')
        return self.gateway_stub.Authenticate(auth_req).token

    def _getResourceInfo(self, endpoint, fileid, userid):
        ref = self._getReference(endpoint, fileid)
        request = storage_provider.ListContainerRequest(ref=ref)
        token = self._getToken(userid)
        stat_info = self.gateway_stub.Stat(request=storage_provider.StatRequest(ref=ref),
                                           metadata=[('x-access-token', token)])
        return stat_info.info

    def _getShareGrant(self, grantee_type, share_permissions, idp, grantee):
        user_id = identity_res.UserId(idp=idp, opaque_id=grantee)
        resources_grantee = storage_resources.Grantee(id=user_id, type=grantee_type)
        return sharing_res.ShareGrant(permissions=share_permissions, grantee=resources_grantee)

    def _getGranteeType(self, grantee_type):
        if grantee_type is "user":
            return storage_resources.GranteeType.GRANTEE_TYPE_USER
        if grantee_type is "group":
            return storage_resources.GranteeType.GRANTEE_TYPE_GROUP
        raise Exception("Invalid grantee type")

    def _getSharePermissions(self, role):
        if role is "viewer":
            permissions = storage_resources.ResourcePermissions(get_path=True,
                                                                initiate_file_download=True,
                                                                list_file_versions=True,
                                                                list_container=True,
                                                                stat=True)
            return sharing_res.SharePermissions(permissions=permissions)
        if role is "editor":
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
