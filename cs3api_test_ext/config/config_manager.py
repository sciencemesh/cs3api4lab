import configparser


class ConfigManager:
    config = {}

    def __init__(self, file_name):
        config_parser = configparser.ConfigParser()
        try:
            with open(file_name) as fdconf:
                config_parser.read_file(fdconf)
            self.config = {
                "reva_host": config_parser.get('cs3', 'reva_host'),
                "auth_token_validity": config_parser.get('cs3', 'auth_token_validity'),
                "user_id": config_parser.get('cs3', 'user_id'),
                "endpoint": config_parser.get('cs3', 'endpoint'),
                "secure_channel": config_parser.getboolean('cs3', 'secure_channel'),
                "client_cert": config_parser.get('cs3', 'client_cert'),
                "client_key": config_parser.get('cs3', 'client_key'),
                "ca_cert": config_parser.get('cs3', 'ca_cert'),
                "chunksize": config_parser.get('io', 'chunksize'),
                "client_id": config_parser.get('cs3', 'client_id'),
                "client_secret": config_parser.get('cs3', 'client_secret'),
                "home_dir": config_parser.get('cs3', 'home_dir'),
                "login_type": config_parser.get('cs3', 'login_type'),
                "file_path": config_parser.get('cs3', 'file_path'),
                "receiver_id": config_parser.get('cs3', 'receiver_id'),
                "receiver_idp": config_parser.get('cs3', 'receiver_idp'),
                "receiver_role": config_parser.get('cs3', 'receiver_role'),
                "receiver_grantee_type": config_parser.get('cs3', 'receiver_grantee_type')
            }
        except (KeyError, configparser.NoOptionError):
            print("Missing option or missing configuration, check the test.conf file")
            raise
