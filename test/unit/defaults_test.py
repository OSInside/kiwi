import logging
from mock import patch

import sys
from mock import MagicMock
from pytest import fixture

from .test_helper import argv_kiwi_tests

from kiwi.defaults import Defaults
from kiwi.defaults import grub_loader_type
from kiwi.defaults import shim_loader_type


class TestDefaults:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

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
        profile = MagicMock()
        self.defaults.to_profile(profile)
        profile.add.assert_any_call('kiwi_align', 1048576)
        profile.add.assert_any_call('kiwi_startsector', 2048)
        profile.add.assert_any_call('kiwi_sectorsize', 512)
        profile.add.assert_any_call(
            'kiwi_revision', self.defaults.get('kiwi_revision')
        )

    def test_get_preparer(self):
        assert Defaults.get_preparer() == \
            'KIWI - https://github.com/OSInside/kiwi'

    def test_get_publisher(self):
        assert Defaults.get_publisher() == 'SUSE LINUX GmbH'

    def test_get_default_shared_cache_location(self):
        assert Defaults.get_shared_cache_location() == 'var/cache/kiwi'

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

    def test_get_live_dracut_modules_from_flag(self):
        assert Defaults.get_live_dracut_modules_from_flag('foo') == \
            ['kiwi-live']
        assert Defaults.get_live_dracut_modules_from_flag('overlay') == \
            ['kiwi-live']
        assert Defaults.get_live_dracut_modules_from_flag('dmsquash') == \
            ['dmsquash-live', 'livenet']

    def test_get_iso_boot_path(self):
        Defaults.set_platform_name('i686')
        assert Defaults.get_iso_boot_path() == 'boot/ix86'
        Defaults.set_platform_name('x86_64')
        assert Defaults.get_iso_boot_path() == 'boot/x86_64'

    @patch('kiwi.defaults.glob.iglob')
    def test_get_unsigned_grub_loader(self, mock_glob):
        mock_glob.return_value = ['/usr/share/grub2/x86_64-efi/grub.efi']
        assert Defaults.get_unsigned_grub_loader('root') == \
            mock_glob.return_value.pop()
        mock_glob.assert_called_once_with('root/usr/share/grub*/*-efi/grub.efi')

    def test_is_x86_arch(self):
        assert Defaults.is_x86_arch('x86_64') is True
        assert Defaults.is_x86_arch('aarch64') is False

    @patch('os.path.exists')
    def test_get_vendor_grubenv(self, mock_path_exists):
        mock_path_exists.return_value = True
        assert Defaults.get_vendor_grubenv('boot/efi') == \
            'boot/efi/EFI/fedora/grubenv'

    def test_get_exclude_list_from_custom_exclude_files(self):
        assert Defaults.get_exclude_list_from_custom_exclude_files(
            '../data/root-dir'
        ) == [
            'usr/bin/qemu-binfmt',
            'usr/bin/qemu-x86_64-binfmt',
            'usr/bin/qemu-x86_64'
        ]

    @patch('yaml.safe_load')
    def test_get_exclude_list_from_custom_exclude_files_is_invalid(
        self, mock_yaml_safe_load
    ):
        mock_yaml_safe_load.return_value = {'invalid': 'artificial'}
        with self._caplog.at_level(logging.WARNING):
            assert Defaults.get_exclude_list_from_custom_exclude_files(
                '../data/root-dir'
            ) == []

    @patch('glob.iglob')
    def test_get_signed_grub_loader(self, mock_iglob):
        def iglob_no_matches(pattern):
            return []

        def iglob_simple_match(pattern):
            if '/boot/efi/EFI/*/grub*.efi' in pattern:
                return ['root_path/boot/efi/EFI/BOOT/grub.efi']
            else:
                return []

        def iglob_custom_binary_match(pattern):
            if '/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed' in pattern:
                return [
                    'root_path'
                    '/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed'
                ]
            else:
                return []

        mock_iglob.side_effect = iglob_no_matches
        assert Defaults.get_signed_grub_loader('root_path') is None

        mock_iglob.side_effect = iglob_simple_match
        assert Defaults.get_signed_grub_loader('root_path') == grub_loader_type(
            filename='root_path/boot/efi/EFI/BOOT/grub.efi',
            binaryname='grub.efi'
        )

        mock_iglob.side_effect = iglob_custom_binary_match
        assert Defaults.get_signed_grub_loader('root_path') == grub_loader_type(
            filename='root_path'
            '/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed',
            binaryname='grubx64.efi'
        )

    @patch('glob.iglob')
    def test_get_mok_manager(self, mock_iglob):
        mock_iglob.return_value = []
        assert Defaults.get_mok_manager('root_path') is None

        mock_iglob.return_value = ['some_glob_result']
        assert Defaults.get_mok_manager('root_path') == 'some_glob_result'

    @patch('glob.iglob')
    def test_get_shim_loader(self, mock_iglob):
        def iglob_simple_match(pattern):
            if '/usr/lib64/efi/shim.efi' in pattern:
                return ['root_path/usr/lib64/efi/shim.efi']
            else:
                return []

        def iglob_custom_binary_match(pattern):
            if '/usr/lib/shim/shimx64.efi.signed' in pattern:
                return [
                    'root_path'
                    '/usr/lib/shim/shimx64.efi.signed'
                ]
            else:
                return []

        assert Defaults.get_shim_loader('root_path') is None

        mock_iglob.side_effect = iglob_simple_match
        assert Defaults.get_shim_loader('root_path') == shim_loader_type(
            filename='root_path'
            '/usr/lib64/efi/shim.efi',
            binaryname='shim.efi'
        )

        mock_iglob.side_effect = iglob_custom_binary_match
        assert Defaults.get_shim_loader('root_path/usr/lib/shim/shimx64.efi.signed') == shim_loader_type(
            filename='root_path'
            '/usr/lib/shim/shimx64.efi.signed',
            binaryname='shimx64.efi'
        )
