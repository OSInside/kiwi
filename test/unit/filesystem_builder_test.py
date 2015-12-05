from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.filesystem_builder import FileSystemBuilder


class TestFileSystemBuilder(object):
    @patch('kiwi.filesystem_builder.FileSystemSetup')
    def setup(self, mock_fs_setup):
        self.loop_provider = mock.Mock()
        self.loop_provider.get_device = mock.Mock(
            return_value='/dev/loop1'
        )
        self.loop_provider.create = mock.Mock()

        self.filesystem = mock.Mock()
        self.filesystem.create_on_device = mock.Mock()
        self.filesystem.create_on_file = mock.Mock()
        self.filesystem.sync_data = mock.Mock()

        self.xml_state = mock.Mock()
        self.xml_state.get_build_type_name = mock.Mock(
            return_value='ext3'
        )
        self.xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
        )
        self.xml_state.build_type.get_target_blocksize = mock.Mock(
            return_value=4096
        )
        fs_setup = mock.Mock()
        fs_setup.get_size_mbytes = mock.Mock(
            return_value=42
        )
        mock_fs_setup.return_value = fs_setup
        self.fs = FileSystemBuilder(
            self.xml_state, 'target_dir', 'source_dir'
        )

    @raises(KiwiFileSystemSetupError)
    def test_create_unknown_filesystem(self):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='super-fs'
        )
        xml_state.xml_data.get_name = mock.Mock(
            return_value='myimage'
        )
        fs = FileSystemBuilder(
            xml_state, 'target_dir', 'source_dir'
        )
        fs.create()

    @raises(KiwiFileSystemSetupError)
    def test_no_filesystem_configured(self):
        xml_state = mock.Mock()
        xml_state.get_build_type_name = mock.Mock(
            return_value='pxe'
        )
        xml_state.build_type.get_filesystem = mock.Mock(
            return_value=None
        )
        FileSystemBuilder(xml_state, 'target_dir', 'source_dir')

    @patch('kiwi.filesystem_builder.LoopDevice')
    @patch('kiwi.filesystem_builder.FileSystem.new')
    def test_create_on_loop(self, mock_fs, mock_loop):
        mock_fs.return_value = self.filesystem
        mock_loop.return_value = self.loop_provider
        self.fs.create()
        mock_loop.assert_called_once_with(
            'target_dir/myimage.ext3', 42, 4096
        )
        self.loop_provider.create.assert_called_once_with()
        mock_fs.assert_called_once_with(
            'ext3', self.loop_provider, 'source_dir', None
        )
        self.filesystem.create_on_device.assert_called_once_with(None)
        self.filesystem.sync_data.assert_called_once_with(
            ['image', '.profile', '.kconfig', 'var/cache/kiwi']
        )

    @patch('kiwi.filesystem_builder.FileSystem.new')
    @patch('kiwi.filesystem_builder.DeviceProvider')
    def test_create_on_file(self, mock_provider, mock_fs):
        provider = mock.Mock()
        mock_provider.return_value = provider
        mock_fs.return_value = self.filesystem
        self.fs.requested_filesystem = 'squashfs'
        self.fs.filename = 'target_dir/myimage.squashfs'
        self.fs.create()
        mock_fs.assert_called_once_with(
            'squashfs', provider, 'source_dir', None
        )
        self.filesystem.create_on_file.assert_called_once_with(
            'target_dir/myimage.squashfs', None
        )
