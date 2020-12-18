"""
cs3_share_api.py

CS3 Share API for the JupyterLab Extension

Authors:
"""
import mimetypes
from datetime import datetime

import urllib.parse
import cs3.sharing.collaboration.v1beta1.collaboration_api_pb2 as sharing
import cs3.sharing.collaboration.v1beta1.resources_pb2 as sharing_res
import cs3.storage.provider.v1beta1.provider_api_pb2 as storage_provider
import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
import cs3.identity.user.v1beta1.resources_pb2 as identity_res
import cs3.rpc.v1beta1.code_pb2 as cs3_code
import grpc

from IPython.utils import tz

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.file_utils import FileUtils
from cs3api4lab.common.strings import *
from cs3api4lab.config.config_manager import Cs3ConfigManager
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.exception.exceptions import *


class Cs3ShareApi:
    cs3_api = None
    log = None
    auth = None
    config = {}
    file_api = None
    date_fmt = '%Y-%m-%dT%H:%M:%SZ'

    TYPE_FILE = 1
    TYPE_DIRECTORY = 2

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)

        self.file_api = Cs3FileApi(log)

        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = grpc_gateway.GatewayAPIStub(intercept_channel)
        return

    def create(self, endpoint, file_path, grantee, idp, role=Role.VIEWER, grantee_type=Grantee.USER):
        share_permissions = self._get_share_permissions(role)
        grantee_type_enum = self._get_grantee_type(grantee_type)
        share_grant = self._get_share_grant(grantee_type_enum, share_permissions, idp, grantee)
        resource_info = self._get_resource_info(endpoint, file_path)
        create_request = sharing.CreateShareRequest(resource_info=resource_info, grant=share_grant)
        token = self.get_token()
        create_response = self.cs3_api.CreateShare(request=create_request,
                                                   metadata=[('x-access-token', token)])
        if create_response.status.code == cs3_code.CODE_OK:
            self.log.info("Created share: " + endpoint + file_path + " for " + idp + ":" + grantee)
            self.log.info(create_response)
            return self._map_given_share(create_response.share)
        if create_response.status.code == cs3_code.CODE_INTERNAL:
            raise ShareAlreadyExistsError("Error creating share: "
                                          + endpoint + file_path
                                          + " for " + idp + ":" + grantee)

    def list_dir_model(self):
        list_response = self._list()
        return self._map_shares_to_model(list_response)

    def _list(self):
        list_request = sharing.ListSharesRequest()
        list_response = self.cs3_api.ListShares(request=list_request,
                                                metadata=[('x-access-token', self.get_token())])
        if self._is_code_ok(list_response):
            self.log.info("List shares response for user: " + self.config['client_id'])
            self.log.info(list_response)
        else:
            self.log.error("Error listing shares response for user: " + self.config['client_id'])
            self._handle_error(list_response)
        return list_response

    def list_grantees_for_file(self, file_path):
        # fixme
        stat = self.file_api.stat(file_path, self.config['client_id'])
        resource_id = storage_resources.ResourceId(storage_id=stat['inode']['storage_id'],
                                                   opaque_id=stat['inode']['opaque_id'])
        resource_filter = sharing.ListSharesRequest.Filter(
            resource_id=resource_id,
            type=sharing.ListSharesRequest.Filter.Type.TYPE_RESOURCE_ID)
        list_request = sharing.ListSharesRequest(filters=[resource_filter])
        shares_response = self.cs3_api.ListShares(request=list_request,
                                                  metadata=[('x-access-token', self.get_token())])
        if self._is_code_ok(shares_response):
            self.log.info("Successfully retrieved grantees for file: " + file_path)
            self.log.info(shares_response)
        else:
            self.log.error("Error retrieving grantees for file: " + file_path)
            self._handle_error(shares_response)
        if not shares_response.shares:
            return []
        share = shares_response.shares[0]
        file_info = {
            "resource_id": {
                "storage_id": share.resource_id.storage_id,
                "opaque_id": self._purify_file_path(share.resource_id.opaque_id)
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
        shares = []
        for share in shares_response.shares:
            share_info = {
                "opaque_id": share.id.opaque_id,
                "grantee": {
                    "idp": share.grantee.id.idp,
                    "opaque_id": share.grantee.id.opaque_id,
                    "permissions": self._resolve_share_permissions(share)
                }
            }
            shares.append(share_info)

        response = {"file_info": file_info, "shares": shares}
        return response

    def _decode_file_path(self, file_path):
        """
        Decodes file path, as the CS3 API contains URL encoded paths
        """
        return urllib.parse.unquote(file_path)

    def _purify_file_path(self, file_path):
        """
        Removes 'fileid-' prefix included in file path from CS3 API response
        """
        return self._decode_file_path(file_path.replace('fileid-' + self.config['client_id'], ''))

    def remove(self, share_id):
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        remove_request = sharing.RemoveShareRequest(ref=ref)
        remove_response = self.cs3_api.RemoveShare(request=remove_request,
                                                   metadata=[('x-access-token', self.get_token())])
        if remove_response.status.code == cs3_code.CODE_OK:
            self.log.info("Successfully removed share with ID: " + share_id)
            self.log.info(remove_response)
            return
        else:
            raise ShareNotExistsError("Error removing share with ID: " + share_id)

    def update(self, share_id, role):
        share_permissions = self._get_share_permissions(role)
        share_id_object = sharing_res.ShareId(opaque_id=share_id)
        ref = sharing_res.ShareReference(id=share_id_object)
        update_request = sharing.UpdateShareRequest(ref=ref,
                                                    field=sharing.UpdateShareRequest.UpdateField(
                                                        permissions=share_permissions))
        update_response = self.cs3_api.UpdateShare(request=update_request,
                                                   metadata=[('x-access-token', self.get_token())])
        if update_response.status.code == cs3_code.CODE_OK:
            self.log.info("Successfully updated share: " + share_id + " with role: " + role)
            self.log.info(update_response)
            return
        if update_response.status.code == cs3_code.CODE_INTERNAL:
            raise ShareNotExistsError("Error updating share: " + share_id)
            # self._handle_error(update_response)

    def list_received(self):
        self.log.info("Listing received shares")
        list_request = sharing.ListReceivedSharesRequest()
        list_response = self.cs3_api.ListReceivedShares(request=list_request,
                                                        metadata=[('x-access-token', self.get_token())])
        if self._is_code_ok(list_response):
            self.log.info("Retrieved received shares for user: " + self.config['client_id'])
            self.log.info(list_response)
        else:
            self.log.error("Error retrieving received shares for user: " + self.config['client_id'])
            self._handle_error(list_response)
        return self._map_shares_to_model(list_response, received=True)

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
        update_response = self.cs3_api.UpdateReceivedShare(request=update_request,
                                                           metadata=[('x-access-token', self.get_token())])
        if self._is_code_ok(update_response):
            self.log.info("Successfully updated share: " + share_id + " with state " + state)
            self.log.info(update_response)
        else:
            self.log.error("Error updating received share: " + share_id + " with state " + state)
            self._handle_error(update_response)
        return

    def _resolve_share_permissions(self, share):
        has_move_permission = share.permissions.permissions.move is True
        has_delete_permission = share.permissions.permissions.delete is True
        if has_move_permission and has_delete_permission:
            return Role.EDITOR
        else:
            return Role.VIEWER

    def _get_resource_info(self, endpoint, file_id):
        ref = FileUtils.get_reference(file_id, endpoint)
        token = self.get_token()
        stat_info = self.cs3_api.Stat(request=storage_provider.StatRequest(ref=ref),
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
        raise InvalidTypeError("Invalid grantee type")

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
            raise InvalidTypeError("Invalid role")

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

        raise InvalidTypeError("Invalid share state")

    def _is_code_ok(self, response):
        return response.status.code == cs3_code.CODE_OK

    def _handle_error(self, response):
        self.log.error(response)
        raise Exception("Incorrect server response: " + response.status.message)

    def get_token(self):
        return self.auth.authenticate()

    def _map_shares_to_model(self, list_response, received=False):

        respond_model = self._create_respond_model()
        path_list = []
        for share in list_response.shares:
            if received:
                share = share.share

            stat = self.file_api.stat(share.resource_id.opaque_id, share.resource_id.storage_id)

            if stat['type'] == self.TYPE_FILE:
                if hasattr(share.permissions.permissions, 'initiate_file_download') and share.permissions.permissions.initiate_file_download is False:
                    continue
                model = self._map_share_to_file_model(share, stat)
            else:
                if hasattr(share.permissions.permissions, 'list_container') and share.permissions.permissions.list_container is False:
                    continue
                model = self._map_share_to_dir_model(share, stat)

            if model['path'] not in path_list:
                respond_model['content'].append(model)
                path_list.append(model['path'])

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
        if hasattr(share.permissions.permissions, 'initiate_file_upload') and share.permissions.permissions.initiate_file_upload is True:
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
