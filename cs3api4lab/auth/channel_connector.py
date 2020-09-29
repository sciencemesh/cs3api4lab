import sys
import grpc
from traitlets.config import LoggingConfigurable
from cs3api4lab.config.config_manager import Cs3ConfigManager


class ChannelConnector(LoggingConfigurable):
    channel = None

    def __new__(cls, *args, **kwargs):
        if cls.channel is None:
            cls.channel = super(ChannelConnector, cls).__new__(cls)
        return cls.channel

    def __init__(self):
        config = Cs3ConfigManager().config
        secure_channel = bool(config['secure_channel'])
        if secure_channel:
            try:
                cert = open(config['client_cert'], 'rb').read()
                key = open(config['client_key'], 'rb').read()
                ca_cert = open(config['ca_cert'], 'rb').read()
                credentials = grpc.ssl_channel_credentials(ca_cert, key, cert)
                channel = grpc.secure_channel(config['reva_host'], credentials)
            except:
                ex = sys.exc_info()[0]
                self.log.error('msg="Error create secure channel" reason="%s"' % ex)
                raise IOError(ex)
        else:
            channel = grpc.insecure_channel(config['reva_host'])
        self.channel = channel

