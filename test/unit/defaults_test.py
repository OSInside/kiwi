import sys

import mock

from .test_helper import argv_kiwi_tests

from kiwi.defaults import Defaults


class TestDefaults(object):
    def setup(self):
        self.defaults = Defaults()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def test_get(self):
        assert self.defaults.get('kiwi_align') == 1048576
        assert self.defaults.get('kiwi_startsector') == 2048
        assert self.defaults.get('kiwi_sectorsize') == 512
        assert self.defaults.get('kiwi_inode_size') == 256
        assert self.defaults.get('kiwi_inode_ratio') == 16384
        assert self.defaults.get('kiwi_min_inodes') == 20000
        assert self.defaults.get('kiwi_revision')

    def test_to_profile(self):
        profile = mock.MagicMock()
        self.defaults.to_profile(profile)
        profile.add.assert_any_call('kiwi_align', 1048576)
        profile.add.assert_any_call('kiwi_startsector', 2048)
        profile.add.assert_any_call('kiwi_sectorsize', 512)
        profile.add.assert_any_call(
            'kiwi_revision', self.defaults.get('kiwi_revision')
        )

    def test_get_preparer(self):
        assert Defaults.get_preparer() == 'KIWI - http://suse.github.com/kiwi'

    def test_get_publisher(self):
        assert Defaults.get_publisher() == 'SUSE LINUX GmbH'

    def test_get_default_shared_cache_location(self):
        assert Defaults.get_shared_cache_location() == 'var/cache/kiwi'

    def test_get_custom_shared_cache_location(self):
        sys.argv = [
            sys.argv[0],
            '--shared-cache-dir', '/my/cachedir',
            'system', 'prepare',
            '--description', 'description', '--root', 'directory'
        ]
        assert Defaults.get_shared_cache_location() == 'my/cachedir'
