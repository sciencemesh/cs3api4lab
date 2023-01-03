import os
from jupyter_core.paths import jupyter_config_path
from jupyter_server.services.config import ConfigManager
from traitlets.config import LoggingConfigurable
from traitlets import Unicode, Bool, CInt, Tuple, default


class Config(LoggingConfigurable):

    reva_host = Unicode(
        config=True, help="""Address and port on which the Reva server is listening"""
    )
    client_id = Unicode(
        config=True, allow_none=True, help="""Client login to authenticate in Reva"""
    )
    client_secret = Unicode(
        config=True, allow_none=True, help="""Client password to authenticate in Reva"""
    )
    auth_token_validity = CInt(
        config=True, help="""The lifetime of the authenticating token"""
    )
    endpoint = Unicode(
        config=True, help="""Endpoint for Reva storage provider"""
    )
    mount_dir = Unicode(
        config=True, help="""root directory of the filesystem"""
    )
    home_dir = Unicode(
        config=True, help="""Home directory of the user"""
    )
    root_dir_list = Tuple(
        config=True, allow_none=True,
        help="""list of root dirs, for example https://developer.sciencemesh.io/docs/iop/deployment/kubernetes/providers/ root dirs are "/home,/reva"""
    )
    chunk_size = CInt(
        config=True, help="""Size of the downloaded fragment from Reva"""
    )
    secure_channel = Bool(
        config=True, help="""Secure channel flag"""
    )
    authenticator_class = Unicode(
        config=True, help="""Authenticator class"""
    )
    login_type = Unicode(
        config=True, help="""Reva login type"""
    )
    locks_expiration_time = CInt(
        config=True, help="""File lock lifetime"""
    )
    client_key = Unicode(
        config=True, allow_none=True, help="""Private key file path"""
    )
    client_cert = Unicode(
        config=True, allow_none=True, help="""Public key file path (PEM-encoded)"""
    )
    ca_cert = Unicode(
        config=True, allow_none=True, help="""Certificate authority file path"""
    )
    enable_ocm = Bool(
        config=True, help="""Flag to enable OCM functionality"""
    )
    tus_enabled = Bool(
        config=True, help="""Flag to enable TUS"""
    )
    eos_file = Unicode(
        config=True, allow_none=True, help="""EOS file location"""
    )
    kernel_path = Unicode(
        config=True, help="""Path where the kernel starts"""
    )
    eos_token = Unicode(
        config=True, allow_none=True, help="""EOS token"""
    )
    oauth_file = Unicode(
        config=True, allow_none=True, help="""Path for OAuth file"""
    )
    oauth_token = Unicode(
        config=True, allow_none=True, help="""OAuth token"""
    )
    locks_api = Unicode(
        config=True, allow_none=False, help="""Locking API implementation to choose from 'cs3' (cs3apis 
        grpc locks) and 'metadata' (file arbitrary metadata, the default one)""",
    )
    dev_env = Bool(
        config=True, allow_none=True, default_value=False, help=""""This is a temporary variable to determine whether this is dev environment"""
    )

    @default("reva_host")
    def _reva_host_default(self):
        return self._get_config_value("reva_host")

    @default("client_id")
    def _client_id_default(self):
        return self._get_config_value("client_id")

    @default("client_secret")
    def _client_secret_default(self):
        return self._get_config_value("client_secret")

    @default("auth_token_validity")
    def _auth_token_validity_default(self):
        return self._get_config_value("auth_token_validity")

    @default("endpoint")
    def _endpoint_default(self):
        return self._get_config_value("endpoint")

    @default("mount_dir")
    def _mount_dir_default(self):
        return self._get_config_value("mount_dir")

    @default("home_dir")
    def _home_dir_default(self):
        return self._get_config_value("home_dir")

    @default("root_dir_list")
    def _root_dir_list_default(self):
        root_dir_list = self._get_config_value("root_dir_list")
        if len(root_dir_list) > 0 and type(root_dir_list) is str:
            root_dir_list = tuple(dir.strip() for dir in root_dir_list.split(','))
        return root_dir_list

    @default("chunk_size")
    def _chunk_size_default(self):
        return self._get_config_value("chunk_size")

    @default("secure_channel")
    def _secure_channel_default(self):
        return self._get_config_value("secure_channel") in ["true", True]

    @default("authenticator_class")
    def _authenticator_class_default(self):
        return self._get_config_value("authenticator_class")

    @default("login_type")
    def _login_type_default(self):
        return self._get_config_value("login_type")

    @default("locks_expiration_time")
    def _locks_expiration_time_default(self):
        return self._get_config_value("locks_expiration_time")

    @default("client_key")
    def _client_key_default(self):
        return self._get_config_value("client_key")

    @default("client_cert")
    def _client_cert_default(self):
        return self._get_config_value("client_cert")

    @default("ca_cert")
    def _ca_cert_default(self):
        return self._get_config_value("ca_cert")

    @default("tus_enabled")
    def _tus_enabled_default(self):
        return self._get_config_value("tus_enabled") in ["true", True]

    @default("enable_ocm")
    def _enable_ocm_default(self):
        return self._get_config_value("enable_ocm") in ["true", True]

    @default("kernel_path")
    def _kernel_path_default(self):
        return self._get_config_value("kernel_path")

    @default("eos_file")
    def _eos_file_default(self):
        return self._get_config_value("eos_file")

    @default("eos_token")
    def _eos_token_default(self):
        return self._get_config_value("eos_token")

    @default("oauth_file")
    def _oauth_file_default(self):
        return self._get_config_value("oauth_file")

    @default("oauth_token")
    def _oauth_token_default(self):
        return self._get_config_value("oauth_token")

    @default("locks_api")
    def _locks_api(self):
        return self._get_config_value("locks_api")

    @default("dev_env")
    def _dev_env_default(self):
        return self._get_config_value("dev_env") in ["true", True]

    def _get_config_value(self, key):
        env = os.getenv("CS3_" + key.upper())
        if env:
            return env
        elif self._file_config(key) is not None:
            return self._file_config(key)
        elif self._default_config[key] is not None:
            return self._default_config[key]
        else:
            return None

    __config_dir = "jupyter-config"
    __config_file_name = 'jupyter_cs3_config'
    __file_config = None

    def _file_config(self, key):
        if self.__file_config is None:
            config_path = jupyter_config_path()
            if self.__config_dir not in config_path:
                # add self._config_dir to the front, if set manually
                config_path.insert(0, os.path.join(os.getcwd(),
                                                   self.__config_dir))  # might be os.path.join(os.getcwd(), 'cs3api4lab', self.__config_dir) depending on the environment setup"
            cm = ConfigManager(read_config_path=config_path)
            try:
                config_file = cm.get(self.__config_file_name)
                self.__file_config = config_file.get("cs3", {})
            except Exception as e:
                self.log.warn("No config files found")
                self.__file_config = {}
        return self.__file_config[key] if key in self.__file_config else None

    _default_config = {
        "reva_host": "localhost:19000",
        "client_id": "einstein",
        "client_secret": "relativity",
        "auth_token_validity": 3600,
        "endpoint": "/",
        "mount_dir": "/home",
        "home_dir": "/",
        "root_dir_list": ['/home', '/reva'],
        "chunk_size": "4194304",
        "secure_channel": True,
        "authenticator_class": "cs3api4lab.auth.RevaPassword",
        "login_type": "basic",
        "locks_expiration_time": 150,
        "client_key": None,
        "client_cert": None,
        "ca_cert": None,
        "tus_enabled": False,
        "enable_ocm": False,
        "kernel_path": "/",
        "eos_file": None,
        "eos_token": None,
        "oauth_file": None,
        "oauth_token": None,
        "locks_api": "metadata",
        "dev_env": False
    }


class Cs3ConfigManager:
    __config_instance = None

    @classmethod
    def get_config(cls):
        if not cls.__config_instance:
            cls.__config_instance = Config()
        return cls.__config_instance

    @classmethod
    def clean(cls):
        cls.__config_instance = None
