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

    def get_user_info(self, idp, opaque_id):
        user_id = id_res.UserId(idp=idp, opaque_id=opaque_id)
        request = user_api.GetUserRequest(user_id=user_id)
        response = self.api.GetUser(request=request)
        if response.status.code == cs3_code.CODE_OK:
            return {"username": response.user.username,
                    "display_name": response.user.display_name,
                    "idp": response.user.id.idp,
                    "opaque_id": response.user.id.opaque_id,
                    "mail": response.user.mail}
        else:
            return {}

    def get_user_info_by_claim(self, claim, value):
        # get user info by mail or username
        request = user_api.GetUserByClaimRequest(claim=claim, value=value)
        response = self.api.GetUserByClaim(request=request)
        if response.status.code == cs3_code.CODE_OK:
            return {"username": response.user.username,
                    "display_name": response.user.display_name,
                    "idp": response.user.id.idp,
                    "opaque_id": response.user.id.opaque_id,
                    "mail": response.user.mail}
        else:
            return {}

    def find_users_by_query(self, query):
        response = self.api.FindUsers(user_api.FindUsersRequest(filter=query),
                                      metadata=[('x-access-token', self.auth.authenticate())])
        ocm_response = self.invite_api.FindAcceptedUsers(ia.FindAcceptedUsersRequest(filter=query),
                                                         metadata=[('x-access-token', self.auth.authenticate())])
        ocm_users = []
        for user in ocm_response.accepted_users:
            ocm_users.append({"username": "",
                              "display_name": user.display_name,
                              "idp": user.id.idp,
                              "opaque_id": user.id.opaque_id,
                              "mail": user.mail})
        users = []
        for user in response.users:
            users.append({"username": user.username,
                          "display_name": user.display_name,
                          "idp": user.id.idp,
                          "opaque_id": user.id.opaque_id,
                          "mail": user.mail})
        return users + ocm_users
