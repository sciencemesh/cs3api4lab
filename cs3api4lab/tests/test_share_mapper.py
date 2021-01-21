import unittest

from cs3api4lab.api.share_mapper import ShareMapper


class MyTestCase(unittest.TestCase):

    def _dir_model(self):
        return {
            'name': '/', 'path': '/', 'last_modified': '2021-01-13T10:26:49Z', 'created': '2021-01-13T10:26:49Z', 'mimetype': None, 'writable': False,
            'type': 'directory', 'size': None, 'content':
                [
                    {
                        'name': 'test_share_file.txt',
                        'path': '/reva/einstein/test_share_file.txt',
                        'last_modified': '2021-01-13T09:31:46Z',
                        'created': '2021-01-13T09:31:46Z',
                        'content': None,
                        'format': None,
                        'writable': False,
                        'size': 14,
                        'type': 'file',
                        'mimetype': 'text/plain'
                    },
                    {
                        'name': 'test_share_dir',
                        'path': '/reva/einstein/test_share_dir',
                        'last_modified': '2021-01-13T09:32:50Z',
                        'created': '2021-01-13T09:32:50Z',
                        'content': None,
                        'format': None,
                        'writable': False,
                        'size': None,
                        'type': 'directory',
                        'mimetype': None
                    },
                    {
                        'name': 'share_file.txt',
                        'path': '/reva/mileva/share_file.txt',
                        'last_modified': '2021-01-13T09:31:46Z',
                        'created': '2021-01-13T09:31:46Z',
                        'content': None,
                        'format': None,
                        'writable': False,
                        'size': 14,
                        'type': 'file',
                        'mimetype': 'text/plain'
                    },
                ]
            , 'format': 'json'}

    def test_remap_dir_model(self):
        share_mapper = ShareMapper().get_mapper()

        remap_dir_model = share_mapper.remap_dir_model(self._dir_model())
        self.assertEqual(remap_dir_model['content'][0]['path'], '/test_share_file.txt')
        self.assertEqual(remap_dir_model['content'][1]['path'], '/test_share_dir')
        self.assertEqual(remap_dir_model['content'][2]['path'], '/share_file.txt')

    def test_remap_path(self):
        share_mapper = ShareMapper().get_mapper()
        share_mapper.remap_dir_model(self._dir_model())

        dst = share_mapper.remap_path('/test_share_file.txt')
        self.assertEqual('/reva/einstein/test_share_file.txt', dst)

        dst = share_mapper.remap_path('/share_file.txt')
        self.assertEqual('/reva/mileva/share_file.txt', dst)

    def test_remap_non_exits_path(self):
        share_mapper = ShareMapper().get_mapper()
        share_mapper.remap_dir_model(self._dir_model())

        dst = share_mapper.remap_path('/einstein/dummy_file.txt')
        self.assertEqual(dst, '/einstein/dummy_file.txt')


if __name__ == '__main__':
    unittest.main()
