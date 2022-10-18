import cs3.identity.user.v1beta1.resources_pb2 as id_res
import cs3.identity.user.v1beta1.user_api_pb2 as user_api
import cs3.identity.user.v1beta1.user_api_pb2_grpc as user_api_grpc
import cs3.ocm.invite.v1beta1.invite_api_pb2 as ia
import cs3.ocm.invite.v1beta1.invite_api_pb2_grpc as iag
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.config.config_manager import Cs3ConfigManager
import cs3.rpc.v1beta1.code_pb2 as cs3_code


class Cs3UserApi:

    def __init__(self, log):
        channel = ChannelConnector.get_channel()
        self.api = user_api_grpc.UserAPIStub(channel)
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=log)
        self.invite_api = iag.InviteAPIStub(channel)

    def get_user(self, idp, opaque_id):
        user_info = self.get_user_info(idp, opaque_id)

        if not user_info and self.config.enable_ocm:
            user_info = self.find_accepted_users(opaque_id)

        return user_info

    def get_user_info(self, idp, opaque_id):
        user_id = id_res.UserId(idp=idp, opaque_id=opaque_id)
        request = user_api.GetUserRequest(user_id=user_id, skip_fetching_user_groups=True)
        response = self.api.GetUser(request=request)

        if response.status.code == cs3_code.CODE_OK:
            return {"username": response.user.username,
                    "display_name": response.user.display_name,
                    "full_name": response.user.display_name + " (" + response.user.username + ")",
                    "idp": response.user.id.idp,
                    "opaque_id": response.user.id.opaque_id,
                    "mail": response.user.mail}

        return {}

    def find_accepted_users(self, opaque_id):
        if self.config.enable_ocm:
            ocm_response = self.invite_api.FindAcceptedUsers(ia.FindAcceptedUsersRequest(filter=opaque_id),
                                                             metadata=[('x-access-token', self.auth.authenticate())])

            ocm_user = ocm_response.accepted_users.pop(0)
            if ocm_response.status.code == cs3_code.CODE_OK:
                return {
                    "username": "",
                    "display_name": ocm_user.display_name,
                    "full_name": ocm_user.display_name,
                    "idp": ocm_user.id.idp,
                    "opaque_id": ocm_user.id.opaque_id,
                    "mail": ocm_user.mail
                }

        return {}

    def get_user_info_by_claim(self, claim, value):
        # get user info by mail or username
        request = user_api.GetUserByClaimRequest(claim=claim, value=value, skip_fetching_user_groups=True)
        response = self.api.GetUserByClaim(request=request)
        if response.status.code == cs3_code.CODE_OK:
            return {"username": response.user.username,
                    "display_name": response.user.display_name,
                    "full_name": response.user.display_name + " (" + response.user.username + ")",
                    "idp": response.user.id.idp,
                    "opaque_id": response.user.id.opaque_id,
                    "mail": response.user.mail}
        else:
            return {}

    def find_users_by_query(self, query):
        if len(query) < 3:
            return []

        users = []
        user_by_username = self.get_user_info_by_claim('username', query)
        if user_by_username:
            users.append(user_by_username)

        user_by_mail = self.get_user_info_by_claim('mail', query)
        if user_by_mail:
            users.append(user_by_mail)

        response = self.api.FindUsers(user_api.FindUsersRequest(filter=query, skip_fetching_user_groups=True),
                                      metadata=[('x-access-token', self.auth.authenticate())])

        for user in response.users:
            users.append({"username": user.username,
                          "display_name": user.display_name,
                          "full_name": user.display_name + " (" + user.username + ")",
                          "idp": user.id.idp,
                          "opaque_id": user.id.opaque_id,
                          "mail": user.mail})

        ocm_users = []
        if self.config.enable_ocm:
            ocm_response = self.invite_api.FindAcceptedUsers(ia.FindAcceptedUsersRequest(filter=query),
                                                             metadata=[('x-access-token', self.auth.authenticate())])

            for user in ocm_response.accepted_users:
                ocm_users.append({"username": "",
                                  "display_name": user.display_name,
                                  "full_name": user.display_name,
                                  "idp": user.id.idp,
                                  "opaque_id": user.id.opaque_id,
                                  "mail": user.mail})

        return users + ocm_users
