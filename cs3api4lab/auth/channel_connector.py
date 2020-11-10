import sys
import grpc
import distutils.util as utils
from traitlets.config import LoggingConfigurable
from cs3api4lab.config.config_manager import Cs3ConfigManager


class Channel(LoggingConfigurable):
    channel = None

    def __init__(self):
        config = Cs3ConfigManager.get_config()
        if type(config['secure_channel']) == bool:
            secure_channel = config['secure_channel']
        else:
            secure_channel = utils.strtobool(config['secure_channel'])
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


class ChannelConnector:
    __channel_instance = None

    @classmethod
    def get_channel(cls):
        if cls.__channel_instance is None:
            cls.__channel_instance = Channel()
        return cls.__channel_instance.channel


