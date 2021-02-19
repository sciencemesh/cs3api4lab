import cs3.identity.user.v1beta1.resources_pb2 as id_res
import cs3.identity.user.v1beta1.user_api_pb2 as user_api
import cs3.identity.user.v1beta1.user_api_pb2_grpc as user_api_grpc
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.config.config_manager import Cs3ConfigManager


class Cs3UserApi:

    def __init__(self, log):
        channel = ChannelConnector.get_channel()
        self.api = user_api_grpc.UserAPIStub(channel)
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=log)

    def get_user_info(self, idp, opaque_id):
        user_id = id_res.UserId(idp=idp, opaque_id=opaque_id)
        request = user_api.GetUserRequest(user_id=user_id)
        response = self.api.GetUser(request=request)
        return {"username": response.user.username,
                "display_name": response.user.display_name,
                "idp": response.user.id.idp,
                "opaque_id": response.user.id.opaque_id,
                "mail": response.user.mail}

    def get_user_info_by_claim(self, claim, value):
        # get user info by mail or username
        request = user_api.GetUserByClaimRequest(claim=claim, value=value)
        response = self.api.GetUserByClaim(request=request)
        return {"username": response.user.username,
                "display_name": response.user.display_name,
                "idp": response.user.id.idp,
                "opaque_id": response.user.id.opaque_id,
                "mail": response.user.mail}

    def find_users_by_query(self, query):
        response = self.api.FindUsers(user_api.FindUsersRequest(filter=query),
                                      metadata=[('x-access-token', self.auth.authenticate())])
        users = []
        for user in response.users:
            users.append({"username": user.username,
                          "display_name": user.display_name,
                          "idp": user.id.idp,
                          "opaque_id": user.id.opaque_id,
                          "mail": user.mail})
        return users
