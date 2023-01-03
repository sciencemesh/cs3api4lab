"""
cs3_public_share_api.py

CS3 Public Shares API for the JupyterLab Extension

"""
from datetime import datetime as dt

import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
import cs3.sharing.link.v1beta1.resources_pb2 as link_res
import cs3.sharing.link.v1beta1.link_api_pb2 as link_api
import cs3.sharing.link.v1beta1.link_api_pb2_grpc as link_api_grpc
import cs3.types.v1beta1.types_pb2 as cs3_types
import cs3.storage.provider.v1beta1.provider_api_pb2 as storage_provider
import cs3.rpc.v1beta1.code_pb2 as cs3_code

import grpc

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.exception.exceptions import ResourceNotFoundError, ShareAlreadyExistsError, ShareNotFoundError
from cs3api4lab.utils.file_utils import FileUtils
from cs3api4lab.config.config_manager import Cs3ConfigManager
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as grpc_gateway
from cs3api4lab.auth.channel_connector import ChannelConnector


class Cs3PublicShareApi:

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
        return

    def create_public_share(self, endpoint, file_path, password, exp_date, permissions):
        resource_info = self._get_resource_info(endpoint, file_path)
        res_permissions = self._dict_to_permissions(permissions)
        public_share_permissions = link_res.PublicSharePermissions(permissions=res_permissions)
        exp_timestamp = self._get_timestamp(exp_date)
        public_share_grant = link_res.Grant(permissions=public_share_permissions,
                                            password=password,
                                            expiration=exp_timestamp)
        request = link_api.CreatePublicShareRequest(resource_info=resource_info, grant=public_share_grant)
        create_response = self.public_share_api.CreatePublicShare(request=request,
                                                           metadata=[('x-access-token', self.auth.authenticate())])
        if create_response.status.code == cs3_code.CODE_NOT_FOUND:
            raise ResourceNotFoundError(f"resource {file_path} not found")
        elif create_response.status.code == cs3_code.CODE_ALREADY_EXISTS:
            raise ShareAlreadyExistsError("Error creating share: " + endpoint + file_path)
        elif create_response.status.code != cs3_code.CODE_OK:
            self._handle_error(create_response)

        return self._map_public_share(create_response.share)

    def list_public_shares(self):
        request = link_api.ListPublicSharesRequest()
        response = self.public_share_api.ListPublicShares(request=request,
                                                          metadata=[('x-access-token', self.auth.authenticate())])
        if response.status.code != cs3_code.CODE_OK:
            self._handle_error(response)
        return list(map(self._map_public_share, response.share))

    def get_public_share(self, opaque_id, token):
        response = self._get_public_share_response(opaque_id, token)
        return self._map_public_share(response.share)

    def _get_public_share_response(self, opaque_id, token):
        share_id = link_res.PublicShareId(opaque_id=opaque_id)
        public_share_ref = link_res.PublicShareReference(id=share_id, token=token)
        request = link_api.GetPublicShareRequest(ref=public_share_ref)
        public_share_response = self.public_share_api.GetPublicShare(request=request,
                                                    metadata=[('x-access-token', self.auth.authenticate())])
        if public_share_response.status.code != cs3_code.CODE_OK:
            self._handle_error(public_share_response)
        return public_share_response

    def get_public_share_by_token(self, token, password):
        request = link_api.GetPublicShareByTokenRequest(token=token, password=password)
        response = self.public_share_api.GetPublicShareByToken(request=request)
        if response.status.code != cs3_code.CODE_OK:
            self._handle_error(response)
        return self._map_public_share(response.share)

    def update_public_share(self, opaque_id, token, field_type, field_value):
        response = self._get_public_share_response(opaque_id, token)
        share_id = link_res.PublicShareId(opaque_id=opaque_id)
        public_share_ref = link_res.PublicShareReference(id=share_id)

        if field_type == 'permissions':
            permissions = self._dict_to_permissions(field_value)
        else:
            permissions = response.share.permissions.permissions
        public_share_permissions = link_res.PublicSharePermissions(permissions=permissions)

        if field_type == 'password':
            public_share_grant = link_res.Grant(permissions=public_share_permissions,
                                                password=field_value)
        elif field_type == 'exp_date':
            public_share_grant = link_res.Grant(permissions=public_share_permissions,
                                                expiration=self._get_timestamp(field_value))
        else:
            public_share_grant = link_res.Grant(permissions=public_share_permissions)

        update_type = self._get_update_type(field_type)
        if field_type == 'display_name':
            update_info = link_api.UpdatePublicShareRequest.Update(grant=public_share_grant,
                                                                   type=update_type,
                                                                   display_name=field_value)
        else:
            update_info = link_api.UpdatePublicShareRequest.Update(grant=public_share_grant,
                                                                   type=update_type)

        request = link_api.UpdatePublicShareRequest(ref=public_share_ref, update=update_info)
        response = self.public_share_api.UpdatePublicShare(request=request,
                                                           metadata=[('x-access-token', self.auth.authenticate())])
        if response.status.code == cs3_code.CODE_NOT_FOUND:
            raise ShareNotFoundError(f"public share {opaque_id} not found")
        elif response.status.code != cs3_code.CODE_OK:
            self._handle_error(response)
        return response.share

    def remove_public_share(self, opaque_id):
        share_id = link_res.PublicShareId(opaque_id=opaque_id)
        public_share_ref = link_res.PublicShareReference(id=share_id)
        request = link_api.RemovePublicShareRequest(ref=public_share_ref)
        response = self.public_share_api.RemovePublicShare(request=request,
                                                           metadata=[('x-access-token', self.auth.authenticate())])
        if response.status.code == cs3_code.CODE_NOT_FOUND:
            raise ShareNotFoundError(f"public share {opaque_id} not found")
        elif response.status.code != cs3_code.CODE_OK:
            self._handle_error(response)
        return response

    def _get_update_type(self, field):
        if field == 'permissions':
            return link_api.UpdatePublicShareRequest.Update.Type.TYPE_PERMISSIONS
        if field == 'password':
            return link_api.UpdatePublicShareRequest.Update.Type.TYPE_PASSWORD
        if field == 'exp_date':
            return link_api.UpdatePublicShareRequest.Update.Type.TYPE_EXPIRATION
        if field == 'display_name':
            return link_api.UpdatePublicShareRequest.Update.Type.TYPE_DISPLAYNAME
        raise Exception("Invalid update type")

    def _date_to_seconds(self, date_str):
        return int(dt.strptime(date_str, '%d-%m-%Y').timestamp())

    def _seconds_to_date(self, seconds):
        return dt.fromtimestamp(seconds).strftime("%d-%m-%Y")

    def _map_public_share(self, share):
        return {
            "opaque_id": share.id.opaque_id,
            "token": share.token,
            "display_name": share.display_name,
            "expiration": self._seconds_to_date(share.expiration.seconds),
            "permissions": self._permissions_to_dict(share),
            "password_protected": share.password_protected,
            "resource_id": {
                "storage_id": share.resource_id.storage_id,
                "opaque_id": share.resource_id.opaque_id,
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

    def _get_full_resource_permissions(self):
        return storage_resources.ResourcePermissions(add_grant=True,
                                                     create_container=True,
                                                     delete=True,
                                                     get_path=True,
                                                     get_quota=True,
                                                     initiate_file_download=True,
                                                     initiate_file_upload=True,
                                                     list_grants=True,
                                                     list_container=True,
                                                     list_file_versions=True,
                                                     list_recycle=True,
                                                     move=True,
                                                     remove_grant=True,
                                                     purge_recycle=True,
                                                     restore_file_version=True,
                                                     restore_recycle_item=True,
                                                     stat=True,
                                                     update_grant=True)

    def _dict_to_permissions(self, perms):
        if not perms:
            return self._get_full_resource_permissions()
        return storage_resources.ResourcePermissions(
            add_grant=perms['add_grant'] if 'add_grant' in perms else False,
            create_container=perms['create_container'] if 'create_container' in perms else False,
            delete=perms['delete'] if 'delete' in perms else False,
            get_path=perms['get_path'] if 'get_path' in perms else False,
            get_quota=perms['get_quota'] if 'get_quota' in perms else False,
            initiate_file_download=perms['initiate_file_download'] if 'initiate_file_download' in perms else False,
            initiate_file_upload=perms['initiate_file_upload'] if 'initiate_file_upload' in perms else False,
            list_grants=perms['list_grants'] if 'list_grants' in perms else False,
            list_container=perms['list_container'] if 'list_container' in perms else False,
            list_file_versions=perms['list_file_versions'] if 'list_file_versions' in perms else False,
            list_recycle=perms['list_recycle'] if 'list_recycle' in perms else False,
            move=perms['move'] if 'move' in perms else False,
            remove_grant=perms['remove_grant'] if 'remove_grant' in perms else False,
            purge_recycle=perms['purge_recycle'] if 'purge_recycle' in perms else False,
            restore_file_version=perms['restore_file_version'] if 'restore_file_version' in perms else False,
            restore_recycle_item=perms['restore_recycle_item'] if 'restore_recycle_item' in perms else False,
            stat=perms['stat'] if 'stat' in perms else False,
            update_grant=perms['update_grant'] if 'update_grant' in perms else False)

    def _permissions_to_dict(self, share):
        perms = {'add_grant': share.permissions.permissions.add_grant,
                 'create_container': share.permissions.permissions.create_container,
                 'delete': share.permissions.permissions.delete,
                 'get_path': share.permissions.permissions.get_path,
                 'get_quota': share.permissions.permissions.get_quota,
                 'initiate_file_download': share.permissions.permissions.initiate_file_download,
                 'initiate_file_upload': share.permissions.permissions.initiate_file_upload,
                 'list_grants': share.permissions.permissions.list_grants,
                 'list_container': share.permissions.permissions.list_container,
                 'list_file_versions': share.permissions.permissions.list_file_versions,
                 'list_recycle': share.permissions.permissions.list_recycle,
                 'move': share.permissions.permissions.move,
                 'remove_grant': share.permissions.permissions.remove_grant,
                 'purge_recycle': share.permissions.permissions.purge_recycle,
                 'restore_file_version': share.permissions.permissions.restore_file_version,
                 'restore_recycle_item': share.permissions.permissions.restore_recycle_item,
                 'stat': share.permissions.permissions.stat,
                 'update_grant': share.permissions.permissions.update_grant}
        return perms

    def _get_timestamp(self, exp_date):
        if exp_date is None or not exp_date:
            return None
        return cs3_types.Timestamp(seconds=self._date_to_seconds(exp_date), nanos=0)

    def _get_resource_info(self, endpoint, file_id):
        ref = FileUtils.get_reference(file_id, endpoint)
        stat_response = self.cs3_api.Stat(request=storage_provider.StatRequest(ref=ref),
                                          metadata=[('x-access-token', self.auth.authenticate())])
        if stat_response.status.code == cs3_code.CODE_OK:
            return stat_response.info
        raise Exception("Can't stat %s:%s" % (file_id, str(stat_response)))

    def _handle_error(self, response):
        self.log.error(response)
        raise Exception("Incorrect server response: " +
                        response.status.message)
