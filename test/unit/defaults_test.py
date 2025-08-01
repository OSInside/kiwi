import logging
from unittest.mock import (
    patch, call
)
import sys
from unittest.mock import MagicMock
from pytest import (
    fixture, raises
)

from .test_helper import argv_kiwi_tests

from kiwi.defaults import Defaults
from kiwi.defaults import grub_loader_type
from kiwi.defaults import shim_loader_type

from kiwi.exceptions import KiwiBootLoaderGrubDataError


class TestDefaults:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.defaults = Defaults()

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

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
        assert mock_glob.return_value[0] in \
            Defaults.get_unsigned_grub_loader('root')[0].filename
        assert mock_glob.call_args_list == [
            call('root/usr/share/grub*/x86_64-efi/grub.efi'),
            call('root/usr/lib/grub*/x86_64-efi/grub.efi'),
            call('root/boot/efi/EFI/*/grubx64.efi'),
            call('root/boot/efi/EFI/*/grubia32.efi'),
            call('root/boot/efi/EFI/*/grubaa64.efi'),
            call('root/boot/efi/EFI/*/grubriscv64.efi')
        ]
        mock_glob.reset_mock()
        mock_glob.return_value = []
        assert Defaults.get_unsigned_grub_loader('root') == []

    def test_is_x86_arch(self):
        assert Defaults.is_x86_arch('x86_64') is True
        assert Defaults.is_x86_arch('aarch64') is False

    @patch('os.path.exists')
    def test_get_vendor_grubenv(self, mock_path_exists):
        mock_path_exists.return_value = True
        assert Defaults.get_vendor_grubenv('boot/efi') == \
            'boot/efi/EFI/fedora/grubenv'

    def test_parse_exclude_file_is_valid(self):
        assert Defaults._parse_exclude_file(
            '../data/root-dir', 'exclude_files.yaml'
        ) == [
            'usr/bin/qemu-binfmt',
            'usr/bin/qemu-x86_64-binfmt',
            'usr/bin/qemu-x86_64'
        ]

    @patch('yaml.safe_load')
    def test_parse_exclude_file_is_invalid(self, mock_yaml_safe_load):
        mock_yaml_safe_load.return_value = {'invalid': 'artificial'}
        with self._caplog.at_level(logging.WARNING):
            assert Defaults._parse_exclude_file(
                '../data/root-dir', 'exclude_files.yaml'
            ) == []

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

    def test_get_exclude_list_from_custom_exclude_files_for_efifatimage(self):
        assert Defaults.get_exclude_list_from_custom_exclude_files_for_efifatimage(
            '../data/root-dir'
        ) == [
            'BOOT/fbia32.efi',
            'BOOT/fbx64.efi',
        ]

    @patch('yaml.safe_load')
    def test_get_exclude_list_from_custom_exclude_files_for_efifatimage_is_invalid(
        self, mock_yaml_safe_load
    ):
        mock_yaml_safe_load.return_value = {'invalid': 'artificial'}
        with self._caplog.at_level(logging.WARNING):
            assert Defaults.get_exclude_list_from_custom_exclude_files_for_efifatimage(
                '../data/root-dir'
            ) == []

    def test_get_exclude_list_for_root_data_sync(self):
        assert Defaults.get_exclude_list_for_root_data_sync() == [
            'image', '.kconfig',
            'run/*', 'tmp/*',
            '.buildenv', 'var/cache/kiwi'
        ]
        assert Defaults.get_exclude_list_for_root_data_sync(no_tmpdirs=False) == [
            'image', '.kconfig',
            '.buildenv', 'var/cache/kiwi'
        ]

    @patch('glob.iglob')
    def test_get_signed_grub_loader(self, mock_iglob):
        def iglob_no_matches(pattern):
            return []

        def iglob_simple_match(pattern):
            if '/boot/efi/EFI/*/grubx64.efi' in pattern:
                return ['root_path/boot/efi/EFI/BOOT/grubx64.efi']
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
        assert Defaults.get_signed_grub_loader('root_path') == []

        mock_iglob.side_effect = iglob_simple_match
        assert Defaults.get_signed_grub_loader('root_path') == [
            grub_loader_type(
                filename='root_path/boot/efi/EFI/BOOT/grubx64.efi',
                binaryname='grubx64.efi',
                targetname='bootx64.efi'
            )
        ]

        mock_iglob.side_effect = iglob_custom_binary_match
        assert Defaults.get_signed_grub_loader('root_path') == [
            grub_loader_type(
                filename='root_path'
                '/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed',
                binaryname='grubx64.efi',
                targetname='bootx64.efi'
            )
        ]

    @patch('glob.iglob')
    def test_get_mok_manager(self, mock_iglob):
        mock_iglob.return_value = []
        assert Defaults.get_mok_manager('root_path') == []

        def iglob_match(pattern):
            if pattern == 'root_path/boot/efi/EFI/*/mm*.efi':
                return ['some']
            return []

        mock_iglob.side_effect = iglob_match

        assert Defaults.get_mok_manager('root_path') == ['some']

    @patch('glob.iglob')
    def test_get_shim_loader(self, mock_iglob):
        def iglob_simple_match(pattern):
            if '/usr/lib64/efi/shim.efi' in pattern:
                return ['root_path/usr/lib64/efi/shim.efi']
            else:
                return []

        def iglob_custom_binary_match(pattern):
            if '/usr/lib/shim/shim*.efi.signed.latest' in pattern:
                return [
                    'root_path'
                    '/usr/lib/shim/shimx64.efi.signed.latest'
                ]
            else:
                return []

        assert Defaults.get_shim_loader('root_path') == []

        mock_iglob.side_effect = iglob_simple_match
        assert Defaults.get_shim_loader('root_path') == [
            shim_loader_type(
                filename='root_path'
                '/usr/lib64/efi/shim.efi',
                binaryname='bootx64.efi'
            )
        ]

        mock_iglob.side_effect = iglob_custom_binary_match
        assert Defaults.get_shim_loader('root_path') == [
            shim_loader_type(
                filename='root_path'
                '/usr/lib/shim/shimx64.efi.signed.latest',
                binaryname='bootx64.efi'
            )
        ]

    @patch('os.path.exists')
    def test_get_snapper_config_template_file(self, mock_os_path_exists):
        mock_os_path_exists.return_value = False
        assert Defaults.get_snapper_config_template_file('root') == ''
        mock_os_path_exists.return_value = True
        assert Defaults.get_snapper_config_template_file('root') == \
            'root/etc/snapper/config-templates/default'

    def test_get_min_volume_mbytes(self):
        assert Defaults.get_min_volume_mbytes('btrfs') == 120
        assert Defaults.get_min_volume_mbytes('xfs') == 300
        assert Defaults.get_min_volume_mbytes('some') == 30

    @patch('glob.iglob')
    def test_get_grub_chrp_loader(self, mock_glob_iglob):
        mock_glob_iglob.return_value = []
        with raises(KiwiBootLoaderGrubDataError):
            Defaults.get_grub_chrp_loader('some-boot')

        mock_glob_iglob.reset_mock()
        mock_glob_iglob.return_value = [
            '/some-boot/boot/grub2/powerpc-ieee1275/grub.elf'
        ]
        assert Defaults.get_grub_chrp_loader('some-boot') == 'grub.elf'
        mock_glob_iglob.assert_called_once_with(
            'some-boot/boot/grub*/powerpc-ieee1275/grub.elf'
        )

    @patch('os.path.exists')
    def test_get_grub_path(self, mock_os_path_exists):
        mock_os_path_exists.return_value = False
        assert Defaults.get_grub_path(
            'root', 'some_file_to_search', False
        ) == ''
