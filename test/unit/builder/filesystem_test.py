import sys
from unittest.mock import (
    patch, Mock
)
from pytest import raises

from ..test_helper import argv_kiwi_tests

import kiwi

from kiwi.defaults import Defaults
from kiwi.exceptions import KiwiFileSystemSetupError
from kiwi.builder.filesystem import FileSystemBuilder


class TestFileSystemBuilder:
    @patch('kiwi.builder.filesystem.FileSystemSetup')
    def setup(self, mock_fs_setup):
        Defaults.set_platform_name('x86_64')

        self.filesystem = Mock()
        self.filesystem.create_on_device = Mock()
        self.filesystem.create_on_file = Mock()
        self.filesystem.sync_data = Mock()

        self.xml_state = Mock()
        self.xml_state.profiles = None
        self.xml_state.get_build_type_unpartitioned_bytes = Mock(
            return_value=0
        )
        self.xml_state.get_fs_mount_option_list = Mock(
            return_value=['async']
        )
        self.xml_state.get_fs_create_option_list = Mock(
            return_value=['-O', 'option']
        )
        self.xml_state.get_build_type_name = Mock(
            return_value='ext3'
        )
        self.xml_state.get_image_version = Mock(
            return_value='1.2.3'
        )
        self.xml_state.xml_data.get_name = Mock(
            return_value='myimage'
        )
        self.xml_state.build_type.get_target_blocksize = Mock(
            return_value=4096
        )

        self.xml_state.build_type.get_squashfscompression = Mock(
            return_value='gzip'
        )

        self.xml_state.build_type.get_erofscompression = Mock(
            return_value='zstd,level=12'
        )

        self.fs_setup = Mock()
        self.fs_setup.get_size_mbytes = Mock(
            return_value=42
        )

        self.setup = Mock()
        kiwi.builder.filesystem.SystemSetup = Mock(
            return_value=self.setup
        )

    @patch('kiwi.builder.filesystem.FileSystemSetup')
    def setup_method(self, cls, mock_fs_setup):
        self.setup()

    def test_create_unknown_filesystem(self):
        self.xml_state.get_build_type_name = Mock(
            return_value='super-fs'
        )
        fs = FileSystemBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        with raises(KiwiFileSystemSetupError):
            fs.create()

    def test_no_filesystem_configured(self):
        self.xml_state.get_build_type_name = Mock(
            return_value='pxe'
        )
        self.xml_state.build_type.get_filesystem = Mock(
            return_value=None
        )
        with raises(KiwiFileSystemSetupError):
            FileSystemBuilder(
                self.xml_state, 'target_dir', 'root_dir'
            )

    @patch('kiwi.builder.filesystem.LoopDevice')
    @patch('kiwi.builder.filesystem.FileSystem.new')
    @patch('kiwi.builder.filesystem.FileSystemSetup')
    def test_create_on_loop(
        self, mock_fs_setup, mock_fs, mock_LoopDevice
    ):
        Defaults.set_platform_name('x86_64')
        mock_fs_setup.return_value = self.fs_setup
        mock_fs.return_value.__enter__.return_value = self.filesystem
        loop_provider = Mock()
        loop_provider.get_device = Mock(
            return_value='/dev/loop1'
        )
        mock_LoopDevice.return_value.__enter__.return_value = loop_provider
        fs = FileSystemBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        fs.create()
        mock_LoopDevice.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.ext3', 42, 4096
        )
        loop_provider.create.assert_called_once_with()
        mock_fs.assert_called_once_with(
            'ext3', loop_provider, 'root_dir/', {
                'mount_options': ['async'],
                'create_options': ['-O', 'option']
            }
        )
        self.filesystem.create_on_device.assert_called_once_with(None)
        self.filesystem.sync_data.assert_called_once_with([
            'image', '.kconfig', 'run/*', 'tmp/*',
            '.buildenv', 'var/cache/kiwi'
        ])
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.filesystem.FileSystem.new')
    @patch('kiwi.builder.filesystem.DeviceProvider')
    def test_create_on_file_erofs(
        self, mock_provider, mock_fs
    ):
        Defaults.set_platform_name('x86_64')
        provider = Mock()
        mock_provider.return_value = provider
        mock_fs.return_value.__enter__.return_value = self.filesystem
        self.xml_state.get_build_type_name = Mock(
            return_value='erofs'
        )
        fs = FileSystemBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        fs.create()
        mock_fs.assert_called_once_with(
            'erofs', provider, 'root_dir', {
                'mount_options': ['async'],
                'create_options': ['-O', 'option'],
                'compression': 'zstd,level=12'
            }
        )
        self.filesystem.create_on_file.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.erofs', None,
            [
                'image', '.kconfig', 'run/*', 'tmp/*',
                '.buildenv', 'var/cache/kiwi'
            ]
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )

    @patch('kiwi.builder.filesystem.FileSystem.new')
    @patch('kiwi.builder.filesystem.DeviceProvider')
    def test_create_on_file_squashfs(
        self, mock_provider, mock_fs
    ):
        Defaults.set_platform_name('x86_64')
        provider = Mock()
        mock_provider.return_value = provider
        mock_fs.return_value.__enter__.return_value = self.filesystem
        self.xml_state.get_build_type_name = Mock(
            return_value='squashfs'
        )
        fs = FileSystemBuilder(
            self.xml_state, 'target_dir', 'root_dir'
        )
        fs.create()
        mock_fs.assert_called_once_with(
            'squashfs', provider, 'root_dir', {
                'mount_options': ['async'],
                'create_options': ['-O', 'option'],
                'compression': 'gzip'
            }
        )
        self.filesystem.create_on_file.assert_called_once_with(
            'target_dir/myimage.x86_64-1.2.3.squashfs', None,
            [
                'image', '.kconfig', 'run/*', 'tmp/*',
                '.buildenv', 'var/cache/kiwi'
            ]
        )
        self.setup.export_package_verification.assert_called_once_with(
            'target_dir'
        )
        self.setup.export_package_list.assert_called_once_with(
            'target_dir'
        )

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()
