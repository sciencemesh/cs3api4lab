import time
import grpc
import asyncio

import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc

from cs3api4lab.auth import check_auth_interceptor
from cs3api4lab.auth.authenticator import Auth
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager

from functools import wraps, partial


class TestApi:
    log = None
    cs3_api = None
    auth = None
    config = None
    lock_manager = None

    def __init__(self, log):
        self.log = log
        self.config = Cs3ConfigManager().get_config()
        self.auth = Auth.get_authenticator(config=self.config, log=self.log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)

        return

    def wrap(func):
        @wraps(func)
        async def run(*args, loop=None, executor=None, **kwargs):
            if loop is None:
                loop = asyncio.get_event_loop()
            pfunc = partial(func, *args, **kwargs)
            return await loop.run_in_executor(executor, pfunc)

        return run

    def test(self):
        time.sleep(5)
        return 'ok'

    @wrap
    def test2(self):
        time.sleep(5)
        return 'ok'

    async def async_test(self):
        loop =  asyncio.get_event_loop()
        await loop.run_in_executor(None, time.sleep, 5)
        #await asyncio.sleep(7)
        return 'ok'