import cs3.sharing.ocm.v1beta1.resources_pb2 as sharing_res
import cs3.storage.provider.v1beta1.resources_pb2 as storage_resources
from cs3api4lab.common.strings import *
from cs3api4lab.exception.exceptions import *

import urllib.parse


class ShareUtils:

    @staticmethod
    def map_grantee(grantee_type):
        if grantee_type == 'user':
            return storage_resources.GranteeType.GRANTEE_TYPE_USER
        if grantee_type == 'group':
            return storage_resources.GranteeType.GRANTEE_TYPE_GROUP

    @staticmethod
    def map_grantee_type(share):
        if share.grantee.type == storage_resources.GranteeType.GRANTEE_TYPE_USER:
            return Grantee.USER
        if share.grantee.type == storage_resources.GranteeType.GRANTEE_TYPE_GROUP:
            return Grantee.GROUP

    @staticmethod
    def map_state(state):
        if isinstance(state, str):
            state = str.lower(state)
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
                return State.PENDING
            elif state == sharing_res.SHARE_STATE_ACCEPTED:
                return State.ACCEPTED
            elif state == sharing_res.SHARE_STATE_REJECTED:
                return State.REJECTED
            elif state == sharing_res.SHARE_STATE_INVALID:
                return State.INVALID

    @staticmethod
    def is_accepted(state):
        return ShareUtils.map_state(state) == State.ACCEPTED

    @staticmethod
    def get_resource_permissions(role):
        if role == Role.VIEWER:
            return storage_resources.ResourcePermissions(get_path=True,
                                                         initiate_file_download=True,
                                                         list_grants=True,
                                                         list_container=True,
                                                         stat=True)
        if role == Role.EDITOR:
            return storage_resources.ResourcePermissions(get_path=True,
                                                         initiate_file_download=True,
                                                         list_grants=True,
                                                         list_container=True,
                                                         stat=True,
                                                         create_container=True,
                                                         delete=True,
                                                         initiate_file_upload=True,
                                                         restore_file_version=True,
                                                         move=True)
        else:
            raise InvalidTypeError("Invalid role")

    @staticmethod
    def map_permissions_to_role(permissions):
        if permissions is None:
            return None
        if permissions.get_path is True and \
                permissions.initiate_file_download is True and \
                permissions.list_container is True and \
                permissions.stat is True and \
                permissions.create_container is True and \
                permissions.delete is True and \
                permissions.initiate_file_upload is True and \
                permissions.restore_file_version is True and \
                permissions.move is True:
            return Role.EDITOR
        else:
            return Role.VIEWER

    @staticmethod
    def decode_file_path(file_path):
        """
        Decodes file path, as the CS3 API contains URL encoded paths
        """
        return urllib.parse.unquote(file_path)

    @staticmethod
    def purify_file_path(file_path, user):
        """
        Transforms 'fileid-user%2F' or '/home/' into '/reva/user'
        """
        if file_path.startswith('/home'):
            return ShareUtils.decode_file_path(file_path.replace('/home', '/reva/' + user))
        return ShareUtils.decode_file_path(file_path.replace('fileid-' + user, '/reva/' + user))

    @staticmethod
    def get_share_info(share):
        return {
            "opaque_id": share.id.opaque_id,
            "grantee": {
                "idp": share.grantee.user_id.idp,
                "opaque_id": share.grantee.user_id.opaque_id,
                "permissions": ShareUtils.map_permissions_to_role(share.permissions.permissions)
            }
        }