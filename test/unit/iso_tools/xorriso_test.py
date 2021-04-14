from mock import patch
from pytest import raises

from kiwi.defaults import Defaults
from kiwi.iso_tools.xorriso import IsoToolsXorrIso

from kiwi.exceptions import KiwiIsoToolError


class TestIsoToolsXorrIso:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.iso_tool = IsoToolsXorrIso('source-dir')

    @patch('kiwi.iso_tools.xorriso.Path.which')
    def test_get_tool_name(self, mock_which):
        mock_which.return_value = 'tool_found'
        assert self.iso_tool.get_tool_name() == 'tool_found'

    @patch('os.path.exists')
    def test_get_tool_name_raises(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiIsoToolError):
            self.iso_tool.get_tool_name()

    @patch('kiwi.iso_tools.xorriso.Path.which')
    def test_init_iso_creation_parameters_isolinux(self, mock_which):
        mock_which.return_value = '/usr/share/syslinux/isohdpfx.bin'
        self.iso_tool.init_iso_creation_parameters(
            {
                'mbr_id': 'app_id',
                'publisher': 'org',
                'preparer': 'preparer',
                'volume_id': 'vol_id'
            }
        )
        mock_which.assert_called_once_with(
            'isohdpfx.bin', [
                '/usr/share/syslinux',
                '/usr/lib/syslinux/bios',
                '/usr/lib/syslinux/modules/bios',
                '/usr/lib/ISOLINUX'
            ]
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
            '-boot_image', 'isolinux',
            'bin_path=boot/x86_64/loader/isolinux.bin',
            '-boot_image', 'isolinux',
            'system_area=/usr/share/syslinux/isohdpfx.bin',
            '-boot_image', 'isolinux', 'partition_table=on',
            '-boot_image', 'any', 'partition_offset=16',
            '-boot_image', 'any', 'cat_path=boot/x86_64/boot.catalog',
            '-boot_image', 'any', 'cat_hidden=on',
            '-boot_image', 'any', 'boot_info_table=on',
            '-boot_image', 'any', 'platform_id=0x00',
            '-boot_image', 'any', 'emul_type=no_emulation',
            '-boot_image', 'any', 'load_size=2048'
        ]

    def test_init_iso_creation_parameters_efi(self):
        self.iso_tool.init_iso_creation_parameters(
            {
                'mbr_id': 'app_id',
                'publisher': 'org',
                'preparer': 'preparer',
                'volume_id': 'vol_id',
                'efi_mode': 'uefi'
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
            'grub2_mbr=source-dir/boot/x86_64//loader/boot_hybrid.img',
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
    def test_add_efi_loader_parameters(self, mock_exists):
        mock_exists.return_value = True
        self.iso_tool.add_efi_loader_parameters()
        assert self.iso_tool.iso_loaders == [
            '-append_partition', '2', '0xef', 'source-dir/boot/x86_64/efi',
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
