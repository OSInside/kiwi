from unittest.mock import (
    patch, Mock, call
)
from pytest import raises

from kiwi.defaults import Defaults
from kiwi.iso_tools.base import IsoToolsBase


class TestIsoToolsBase:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.iso_tool = IsoToolsBase('source-dir')

    def setup_method(self, cls):
        self.setup()

    def test_create_iso(self):
        with raises(NotImplementedError):
            self.iso_tool.create_iso('filename')

    def test_list_iso(self):
        with raises(NotImplementedError):
            self.iso_tool.list_iso('isofile')

    def test_get_tool_name(self):
        with raises(NotImplementedError):
            self.iso_tool.get_tool_name()

    def test_init_iso_creation_parameters(self):
        with raises(NotImplementedError):
            self.iso_tool.init_iso_creation_parameters()

    def test_add_efi_loader_parameters(self):
        with raises(NotImplementedError):
            self.iso_tool.add_efi_loader_parameters('loader_file')

    def test_has_iso_hybrid_capability(self):
        with raises(NotImplementedError):
            self.iso_tool.has_iso_hybrid_capability()

    @patch('kiwi.iso_tools.base.DataSync')
    @patch('kiwi.iso_tools.base.shutil')
    @patch('kiwi.iso_tools.base.Command.run')
    @patch('kiwi.iso_tools.base.Path')
    @patch('os.path.exists')
    def test_setup_media_loader_directory(
        self, mock_exists, mock_Path, mock_command, mock_shutil, mock_sync
    ):
        mock_exists.return_value = True
        data = Mock()
        mock_sync.return_value = data
        self.iso_tool.setup_media_loader_directory(
            'root_dir', 'media_dir', 'openSUSE'
        )
        assert mock_shutil.copy.call_args_list == [
            call(
                'root_dir/usr/share/grub2/i386-pc/eltorito.img',
                'root_dir/image/loader/'
            ),
            call(
                'root_dir/usr/share/grub2/i386-pc/boot_hybrid.img',
                'root_dir/image/loader/'
            )
        ]
        assert mock_command.call_args_list == [
            call(
                command=[
                    'bash', '-c',
                    'cp root_dir/boot/memtest* '
                    'root_dir/image/loader//memtest'
                ], raise_on_error=False
            ),
            call(
                [
                    'bash', '-c',
                    'cp root_dir/etc/bootsplash/themes/openSUSE/'
                    'cdrom/* root_dir/image/loader/'
                ]
            ),
            call(
                [
                    'gfxboot',
                    '--config-file', 'root_dir/image/loader//gfxboot.cfg',
                    '--change-config', 'install::autodown=0'
                ]
            ),
            call(
                [
                    'cp',
                    'root_dir/etc/bootsplash/themes/openSUSE/'
                    'bootloader/message', 'root_dir/image/loader/'
                ]
            )
        ]
        mock_sync.assert_called_once_with(
            'root_dir/image/loader/',
            'media_dir/boot/x86_64/loader'
        )
        data.sync_data.assert_called_once_with(
            options=['-a']
        )
