import logging
from unittest.mock import patch
from pytest import (
    raises, fixture
)

from kiwi.defaults import Defaults
from kiwi.iso_tools.xorriso import IsoToolsXorrIso

from kiwi.exceptions import KiwiIsoToolError


class TestIsoToolsXorrIso:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.iso_tool = IsoToolsXorrIso('source-dir')

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.iso_tools.xorriso.Path.which')
    def test_get_tool_name(self, mock_which):
        mock_which.return_value = 'tool_found'
        assert self.iso_tool.get_tool_name() == 'tool_found'

    @patch('os.path.exists')
    def test_get_tool_name_raises(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiIsoToolError):
            self.iso_tool.get_tool_name()

    @patch('os.path.exists')
    def test_init_iso_creation_parameters_no_hybrid_mbr(
        self, mock_os_path_exists
    ):
        mock_os_path_exists.return_value = False
        with self._caplog.at_level(logging.WARNING):
            self.iso_tool.init_iso_creation_parameters(
                {
                    'mbr_id': 'app_id',
                    'publisher': 'org',
                    'preparer': 'preparer',
                    'volume_id': 'vol_id',
                    'efi_mode': 'uefi',
                    'legacy_bios_mode': True
                }
            )
            assert 'No hybrid MBR file found' in self._caplog.text

    @patch('os.path.exists')
    def test_init_iso_creation_parameters_ppc(self, mock_os_path_exists):
        mock_os_path_exists.return_value = True
        self.iso_tool.arch = 'ppc64le'
        self.iso_tool.init_iso_creation_parameters(
            {
                'mbr_id': 'app_id',
                'publisher': 'org',
                'preparer': 'preparer',
                'volume_id': 'vol_id',
                'efi_mode': 'ofw',
                'legacy_bios_mode': False
            }
        )
        assert self.iso_tool.iso_parameters == [
            '-application_id', 'app_id',
            '-publisher', 'org',
            '-preparer_id', 'preparer',
            '-volid', 'vol_id',
            '-joliet', 'on',
            '-padding', '0',
            '-compliance', 'untranslated_names'
        ]

    @patch('os.path.exists')
    def test_init_iso_creation_parameters_efi(self, mock_os_path_exists):
        mock_os_path_exists.return_value = True
        self.iso_tool.init_iso_creation_parameters(
            {
                'mbr_id': 'app_id',
                'publisher': 'org',
                'preparer': 'preparer',
                'volume_id': 'vol_id',
                'efi_mode': 'uefi',
                'legacy_bios_mode': True
            }
        )
        assert self.iso_tool.iso_parameters == [
            '-application_id', 'app_id',
            '-publisher', 'org',
            '-preparer_id', 'preparer',
            '-volid', 'vol_id',
            '-joliet', 'on',
            '-padding', '0'
        ]
        assert self.iso_tool.iso_loaders == [
            '-boot_image', 'grub',
            'bin_path=boot/x86_64/loader/eltorito.img',
            '-boot_image', 'grub',
            'grub2_mbr=source-dir/boot/x86_64/loader/boot_hybrid.img',
            '-boot_image', 'grub', 'grub2_boot_info=on',
            '-boot_image', 'any', 'partition_offset=16',
            '-boot_image', 'any', 'cat_path=boot/x86_64/boot.catalog',
            '-boot_image', 'any', 'cat_hidden=on',
            '-boot_image', 'any', 'boot_info_table=on',
            '-boot_image', 'any', 'platform_id=0x00',
            '-boot_image', 'any', 'emul_type=no_emulation',
            '-boot_image', 'any', 'load_size=2048'
        ]

    @patch('os.path.exists')
    def test_init_iso_creation_parameters_efi_custom_app_id(
        self, mock_os_path_exists
    ):
        mock_os_path_exists.return_value = True
        self.iso_tool.init_iso_creation_parameters(
            {
                'mbr_id': 'app_id',
                'application_id': 'some_other_app_id',
                'publisher': 'org',
                'preparer': 'preparer',
                'volume_id': 'vol_id',
                'efi_mode': 'uefi',
                'legacy_bios_mode': True
            }
        )
        assert self.iso_tool.iso_parameters == [
            '-application_id', 'some_other_app_id',
            '-publisher', 'org',
            '-preparer_id', 'preparer',
            '-volid', 'vol_id',
            '-joliet', 'on',
            '-padding', '0'
        ]

    def test_add_efi_loader_parameters(self):
        self.iso_tool.add_efi_loader_parameters('target_dir/efi-loader')
        assert self.iso_tool.iso_loaders == [
            '-append_partition', '2', '0xef', 'target_dir/efi-loader',
            '-boot_image', 'any', 'next',
            '-boot_image', 'any',
            'efi_path=--interval:appended_partition_2:all::',
            '-boot_image', 'any', 'platform_id=0xef',
            '-boot_image', 'any', 'emul_type=no_emulation'
        ]

    @patch('kiwi.iso_tools.xorriso.Command.run')
    @patch('kiwi.iso_tools.xorriso.Path.wipe')
    @patch('kiwi.iso_tools.xorriso.Path.which')
    def test_create_iso(self, mock_which, mock_wipe, mock_command):
        mock_which.return_value = '/usr/bin/xorriso'
        self.iso_tool.create_iso('myiso', hidden_files=['hide_me'])
        mock_wipe.assert_called_once_with('myiso')
        mock_command.assert_called_once_with(
            [
                '/usr/bin/xorriso',
                '-outdev', 'myiso',
                '-map', 'source-dir', '/',
                '-chmod', '0755', '/', '--',
                '--', '-find', 'hide_me', '-exec', 'hide', 'on'
            ]
        )

    def test_has_iso_hybrid_capability(self):
        assert self.iso_tool.has_iso_hybrid_capability() is True
