import time
from unittest import TestCase
from cs3api4lab.api.cs3_locks_api import LocksApi
from traitlets.config import LoggingConfigurable
import cs3.storage.provider.v1beta1.resources_pb2 as cs3spr
import cs3.rpc.v1beta1.code_pb2 as cs3code
from cs3api4lab.api.cs3_user_api import Cs3UserApi
from cs3api4lab import CS3APIsManager
from cs3api4lab.api.cs3_file_api import Cs3FileApi
from cs3api4lab.api.cs3_share_api import Cs3ShareApi
from cs3api4lab.auth import RevaPassword
from cs3api4lab.auth.channel_connector import ChannelConnector
from cs3api4lab.config.config_manager import Cs3ConfigManager
import cs3.gateway.v1beta1.gateway_api_pb2_grpc as cs3gw_grpc
import cs3.identity.user.v1beta1.user_api_pb2_grpc as user_api_grpc
from cs3api4lab.api.storage_api import StorageApi
from cs3api4lab.auth import check_auth_interceptor
import grpc


class ExtAuthenticator(RevaPassword):
    def __init__(self, config, log):
        super().__init__(config, log)
        self.config = config
        self.log = log
        channel = ChannelConnector().get_channel()
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(channel)


class ExtCs3File(Cs3FileApi):
    def __init__(self, log, config) -> None:
        self.log = log
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        channel = ChannelConnector().get_channel()
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(channel)
        self.storage_api = ExtStorageApi(log, config)


class ExtCs3ShareApi(Cs3ShareApi):
    def __init__(self, log, config) -> None:
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        self.file_api = ExtCs3File(log, config)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(ChannelConnector().get_channel())
        self.log = log

    def list(self):
        list_response = self.list()
        return self._map_given_shares(list_response)


class ExtUserApi(Cs3UserApi):
    def __init__(self, log, config) -> None:
        self.api = user_api_grpc.UserAPIStub(ChannelConnector().get_channel())
        self.config = config
        self.auth = ExtAuthenticator(log, config)


class ExtStorageApi(StorageApi):
    def __init__(self, log, config) -> None:
        self.log = log
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        channel = ChannelConnector().get_channel()
        auth_interceptor = check_auth_interceptor.CheckAuthInterceptor(log, self.auth)
        intercept_channel = grpc.intercept_channel(channel, auth_interceptor)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(intercept_channel)


class ExtCs3LocksApi(LocksApi):
    def __init__(self, log, config) -> None:
        self.log = log
        self.config = config
        self.auth = ExtAuthenticator(config, log)
        self.cs3_api = cs3gw_grpc.GatewayAPIStub(ChannelConnector().get_channel())
        self.user_api = ExtUserApi(log, config)
        self.file_api = ExtCs3File(log, config)
        self.storage_api = ExtStorageApi(log, config)


class ExtCS3APIsManager(CS3APIsManager):
    def __init__(self, parent, log, config):
        self.cs3_config = config
        self.log = log
        self.file_api = ExtCs3File(log, config)


class TestCs3FileApi(TestCase, LoggingConfigurable):
    config = None

    file_copy_path = '/home/copy-einstein_cernbox.cern.ch_4c510ada-c86b-4815-8820-42cdf82c3d51_test_file.txt'
    file_copy_path2 = '/home/copy-marie_cesnet.cz_f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c_test_file.txt'
    file_path = '/home/test_file.txt'
    file_path_uni = '/reva/einstein/test_file.txt'
    file_path2 = '/home/test_file2.txt'
    locks_file_path = '/home/.locks'
    lock_name = 'copy-einstein_cernbox.cern.ch_4c510ada-c86b-4815-8820-42cdf82c3d51_'
    file_copy_path_uni = '/reva/einstein/copy-einstein_cernbox.cern.ch_4c510ada-c86b-4815-8820-42cdf82c3d51_test_einstein_share_file.txt'

    user_opaque_id_1 = 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c'
    user_idp_1 = 'cesnet.cz'

    user_opaque_id_2 = '4c510ada-c86b-4815-8820-42cdf82c3d51'
    user_idp_2 = 'cernbox.cern.ch'

    editor_role = 'editor'
    endpoint = "/"
    content = f"Lorem ipsum..."

    first_client_id = "einstein"
    first_client_secret = "relativity"

    second_client_id = "marie"
    second_client_secret = "radioactivity"

    def setUp(self):
        config = Cs3ConfigManager.get_config()
        self.client_id = config['client_id']
        self.endpoint = config['endpoint']
        self.storage = Cs3FileApi(self.log)

        self.config = Cs3ConfigManager().get_config()
        self.config_ext = self.config.copy()

        self.locks_api = LocksApi(self.log)
        self.locks_api_ext = ExtCs3LocksApi(self.log, self.config_ext)

        self.storage_new = ExtStorageApi(self.log, self.config)

        self.config["client_id"] = self.first_client_id
        self.config["client_secret"] = self.first_client_secret

        self.config_ext["client_id"] = self.second_client_id
        self.config_ext["client_secret"] = self.second_client_secret

        self.storage = ExtCs3File(self.log, self.config)
        self.share_api = ExtCs3ShareApi(self.log, self.config)

        self.storage_ext = ExtCs3File(self.log, self.config_ext)
        self.share_api_ext = ExtCs3ShareApi(self.log, self.config_ext)

        self.manager_ext = ExtCS3APIsManager(None, self.log, self.config_ext)

    def test_copy_file(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            original_ref = cs3spr.Reference(path=self.file_path)
            copy_stat = self.locks_api.copy_file(original_ref)
            self.assertTrue(copy_stat.status.code == cs3code.CODE_OK)
            self.assertTrue(self.file_copy_path in copy_stat.info.path)
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)
            self._remove_test_file('einstein', self.file_copy_path)

    def test_create_working_copy(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            ref = cs3spr.Reference(path=self.file_path)
            self.locks_api.create_working_copy(ref)
            locks_ref = cs3spr.Reference(path=self.locks_file_path)
            locks_stat = self.locks_api.stat(locks_ref)
            self.assertTrue(locks_stat.status.code == cs3code.CODE_OK)
            locks_content = self.locks_api.get_locks_file_content()
            self.assertTrue(self.file_path_uni in locks_content)
            copy_stat = self.locks_api.stat(self.locks_api.get_unified_file_ref(self.file_copy_path, self.endpoint))
            self.assertTrue('test_file.txt' in copy_stat.info.arbitrary_metadata.metadata['original'])
            self.assertTrue(True)
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)
            self._remove_test_file('einstein', self.file_copy_path)
            self.storage.remove(self.locks_file_path)

    def test_get_copies_info_when_one_copy(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            self.locks_api.create_working_copy(cs3spr.Reference(path=self.file_path))
            copies = self.locks_api.get_copies_info(self.file_path, self.endpoint)
            self.assertFalse(copies == [])
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)

    def test_get_copies_info_when_no_copies(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            copies = self.locks_api.get_copies_info(self.file_path, self.endpoint)
            self.assertTrue(copies == [])
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)

    def test_delete_lock(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            ref = cs3spr.Reference(path=self.file_path)
            self.locks_api.create_working_copy(ref)
            self.locks_api.delete_lock(self.file_copy_path, self.endpoint)
            fr = self.locks_api.get_unified_file_ref(self.file_path, self.endpoint)
            stat = self.locks_api.stat(fr)
            lock = stat.info.arbitrary_metadata.metadata[self.lock_name]
            self.assertTrue(lock == '')
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)


    def test_get_merger(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            self.locks_api.create_working_copy(cs3spr.Reference(path=self.file_path))
            merger = self.locks_api.get_merger(self.file_path, self.endpoint)
            self.assertTrue(merger)
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)

    def test_update_lock(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            self.locks_api.create_working_copy(cs3spr.Reference(path=self.file_path))
            updated = self.locks_api.get_copies_info(self.file_path, self.endpoint)[0]['updated']
            stat = self.locks_api.stat(cs3spr.Reference(path=self.file_copy_path))
            self.locks_api.update_lock(stat.info.id.opaque_id, stat.info.id.storage_id)
            updated_new = self.locks_api.get_copies_info(self.file_path, self.endpoint)[0]['updated']
            self.assertTrue(updated_new > updated)
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)
            self._remove_test_file('einstein', self.file_copy_path)

    def test_check_locks(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            self.locks_api.check_locks()

            self.locks_api.create_working_copy(cs3spr.Reference(path=self.file_path))
            copies = self.locks_api.get_copies_info(self.file_path, self.endpoint)
            self.assertTrue(len(copies) == 1)

            self.locks_api.check_locks()
            copies = self.locks_api.get_copies_info(self.file_path, self.endpoint)
            self.assertTrue(len(copies) == 1)

            time.sleep(60)
            self.locks_api.check_locks()
            copies = self.locks_api.get_copies_info(self.file_path, self.endpoint)
            self.assertTrue(len(copies) == 0)
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)
            self._remove_test_file('einstein', self.file_copy_path)

    def test_on_open_hook_no_copies(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self.locks_api.on_open_hook(self.file_path, self.endpoint)
            copy_stat = self.locks_api.stat(cs3spr.Reference(path=self.file_copy_path_uni))
            self.assertTrue(copy_stat.status.code == cs3code.CODE_NOT_FOUND)
        finally:
            self._remove_test_file('einstein', self.file_path)

    def test_on_open_hook_when_copy(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_share('einstein')
            ref = cs3spr.Reference(path=self.file_path)
            self.locks_api.create_working_copy(ref)
            updated = self.locks_api.get_copies_info(self.file_path, self.endpoint)[0]['updated']
            self.locks_api.on_open_hook(self.file_path, self.endpoint)
            updated_new = self.locks_api.get_copies_info(self.file_path, self.endpoint)[0]['updated']
            self.assertTrue(updated_new > updated)
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)
            self._remove_test_file('einstein', self.locks_file_path)
            self._remove_test_file('einstein', self.file_copy_path)

    def test_on_close_hook_when_closing_copy(self):
        try:
            self._create_test_file('einstein', self.file_path)
            ref = cs3spr.Reference(path=self.file_path)
            self.locks_api.create_working_copy(ref)
            uni_ref = self.locks_api.get_unified_file_ref(self.file_path, self.endpoint)
            stat = self.locks_api.stat(uni_ref)
            lock = stat.info.arbitrary_metadata.metadata[self.lock_name]
            self.assertTrue(lock)
            self.locks_api.on_close_hook(self.file_copy_path, self.endpoint)
            stat = self.locks_api.stat(uni_ref)
            lock = stat.info.arbitrary_metadata.metadata[self.lock_name]
            self.assertTrue(lock == '')
        finally:
            self._remove_test_file('einstein', self.file_path)
            self._remove_test_file('einstein', self.locks_file_path)
            self._remove_test_file('einstein', self.file_copy_path)

    def test_flow(self):
        try:
            self._create_test_file('einstein', self.file_path)
            self._create_test_file('einstein', self.file_path2)
            self._create_share('einstein')

            locks_ref = cs3spr.Reference(path=self.locks_file_path)
            locks_stat = self.locks_api.stat(locks_ref)
            self.assertTrue(locks_stat.status.code == cs3code.CODE_NOT_FOUND)
            ref = cs3spr.Reference(path=self.file_path)
            copy_ref = cs3spr.Reference(path=self.locks_api._get_copy_path(ref))
            stat = self.locks_api.stat(copy_ref)
            self.assertTrue(stat.status.code == cs3code.CODE_NOT_FOUND)

            self.locks_api.on_open_hook(self.file_path, self.endpoint)
            locks_content = self.locks_api.get_locks_file_content()
            self.assertTrue(self.file_path_uni in locks_content)
            stat = self.locks_api.stat(copy_ref)
            self.assertTrue(stat.status.code == cs3code.CODE_OK)
            merger = self.locks_api.get_merger(self.file_path, self.endpoint)

            self.locks_api_ext.on_open_hook(self.file_path_uni, self.endpoint)
            locks_content_marie = self.locks_api_ext.get_locks_file_content()
            self.assertTrue(self.file_path_uni in locks_content_marie)
            copy_ref_marie = cs3spr.Reference(path=self.locks_api_ext._get_copy_path(ref))
            stat_marie = self.locks_api_ext.stat(copy_ref_marie)
            self.assertTrue(stat_marie.status.code == cs3code.CODE_OK)
            merger_marie = self.locks_api_ext.get_merger(self.file_path_uni, self.endpoint)
            self.assertTrue(merger_marie['username'] == 'einstein')
            copies_marie = self.locks_api_ext.get_copies_info(self.file_path_uni, self.endpoint)
            self.assertTrue(len(copies_marie) == 2)

        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)
            self._remove_test_file('einstein', self.file_copy_path)
            self._remove_test_file('einstein', self.locks_file_path)
            self._remove_test_file('marie', self.file_copy_path2)
            self._remove_test_file('marie', self.locks_file_path)

    def test_is_shared_file(self):
        try:
            self._create_test_file('einstein', self.file_path)
            is_not_shared = self.locks_api.is_shared_file(self.file_path, self.endpoint)
            self.assertFalse(is_not_shared)
            self._create_share('einstein')
            is_shared = self.locks_api.is_shared_file(self.file_path, self.endpoint)
            self.assertTrue(is_shared)
        finally:
            self._remove_share('einstein')
            self._remove_test_file('einstein', self.file_path)

    def _create_share(self, creator):
        if creator == self.first_client_id:
            self.share_id = self.share_api.create(self.endpoint,
                                                  self.file_path,
                                                  self.user_opaque_id_1,
                                                  self.user_idp_1,
                                                  self.editor_role)['opaque_id']
        if creator == self.second_client_id:
            self.share_id = self.share_api_ext.create(self.endpoint,
                                                      self.file_path2,
                                                      self.user_opaque_id_2,
                                                      self.user_idp_2,
                                                      self.editor_role)['opaque_id']

    def _create_test_file(self, creator, file_path):
        if creator == self.first_client_id:
            self.storage.write_file(file_path,
                                    self.content,
                                    self.endpoint)
        if creator == self.second_client_id:
            self.storage_ext.write_file(file_path,
                                        self.content,
                                        self.endpoint)

    def _remove_share(self, owner):
        if owner == self.first_client_id:
            self.share_api.remove(self.share_id)
        if owner == self.second_client_id:
            self.share_api_ext.remove(self.share_id)

    def _remove_test_file(self, owner, file_path):
        if owner == self.first_client_id:
            self.storage.remove(file_path, self.endpoint)
        if owner == self.second_client_id:
            self.storage_ext.remove(file_path, self.endpoint)
