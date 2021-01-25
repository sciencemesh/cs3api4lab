import sys
import grpc
import distutils.util as utils
from traitlets.config import LoggingConfigurable
from cs3api4lab.config.config_manager import Cs3ConfigManager


class Channel(LoggingConfigurable):
    channel = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        config = Cs3ConfigManager.get_config()
        if type(config['secure_channel']) == bool:
            secure_channel = config['secure_channel']
        else:
            secure_channel = utils.strtobool(config['secure_channel'])
        if secure_channel:
            try:

                cert = None
                key = None
                ca_cert = None

                if config['client_cert'] is not None and len(config['client_cert']) > 0:
                    cert = open(config['client_cert'], 'rb').read()

                if config['client_cert'] is not None and len(config['client_key']) > 0:
                    key = open(config['client_key'], 'rb').read()

                if config['client_cert'] is not None and len(config['ca_cert']) > 0:
                    ca_cert = open(config['ca_cert'], 'rb').read()

                credentials = grpc.ssl_channel_credentials(root_certificates=ca_cert, private_key=key, certificate_chain=cert)
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
