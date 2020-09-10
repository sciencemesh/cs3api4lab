import sys
import grpc


class ChannelConnector:

    def __init__(self, config, log):
        self.log = log
        self.config = config

    def get_channel(self):
        secure_channel = bool(self.config['secure_channel'])
        if secure_channel:
            try:
                cert = open(self.config['client_cert'], 'rb').read()
                key = open(self.config['client_key'], 'rb').read()
                ca_cert = open(self.config['ca_cert'], 'rb').read()
                credentials = grpc.ssl_channel_credentials(ca_cert, key, cert)
                channel = grpc.secure_channel(self.config['reva_host'], credentials)
            except:
                ex = sys.exc_info()[0]
                self.log.error('msg="Error create secure channel" reason="%s"' % ex)
                raise IOError(ex)
        else:
            channel = grpc.insecure_channel(self.config['reva_host'])
        return channel
