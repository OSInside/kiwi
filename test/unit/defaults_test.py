from mock import patch

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

    @patch('kiwi.defaults.Path.which')
    def test_get_grub_boot_directory_name(self, mock_which):
        mock_which.return_value = 'grub2-install-was-found'
        assert Defaults.get_grub_boot_directory_name(
            lookup_path='lookup_path'
        ) == 'grub2'
        mock_which.return_value = None
        assert Defaults.get_grub_boot_directory_name(
            lookup_path='lookup_path'
        ) == 'grub'

    @patch('kiwi.defaults.sys')
    @patch('kiwi.defaults.reload_module')
    def test_set_python_default_encoding_to_utf8(self, mock_reload, mock_sys):
        mock_sys.version_info.major = 2
        Defaults.set_python_default_encoding_to_utf8()
        mock_reload.assert_called_once_with(mock_sys)
        mock_sys.setdefaultencoding.assert_called_once_with('utf-8')

    def test_get_live_dracut_module_from_flag(self):
        assert Defaults.get_live_dracut_module_from_flag('foo') == \
            'kiwi-live'
        assert Defaults.get_live_dracut_module_from_flag('overlay') == \
            'kiwi-live'
        assert Defaults.get_live_dracut_module_from_flag('dmsquash') == \
            'dmsquash-live livenet'

    @patch('platform.machine')
    def test_get_iso_boot_path(self, mock_machine):
        mock_machine.return_value = 'i686'
        assert Defaults.get_iso_boot_path() == 'boot/ix86'
        mock_machine.return_value = 'x86_64'
        assert Defaults.get_iso_boot_path() == 'boot/x86_64'

    @patch('kiwi.defaults.glob.iglob')
    def test_get_unsigned_grub_loader(self, mock_glob):
        mock_glob.return_value = ['/usr/lib/grub2/x86_64-efi/grub.efi']
        assert Defaults.get_unsigned_grub_loader('root') == \
            mock_glob.return_value.pop()
        mock_glob.assert_called_once_with('root/usr/lib/grub*/*-efi/grub.efi')
