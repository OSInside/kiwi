from nose.tools import *
from mock import patch

import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.filesystem_base import FileSystemBase


class TestFileSystemBase(object):
    def setup(self):
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/loop0'
        )
        self.fsbase = FileSystemBase(provider, 'root_dir')

    @raises(KiwiFileSystemSyncError)
    def test_root_dir_does_not_exist(self):
        fsbase = FileSystemBase(mock.Mock(), 'root_dir_not_existing')
        fsbase.sync_data()

    @raises(KiwiFileSystemSyncError)
    def test_root_dir_not_defined(self):
        fsbase = FileSystemBase(mock.Mock())
        fsbase.sync_data()

    @raises(NotImplementedError)
    def test_create_on_device(self):
        self.fsbase.create_on_device('/dev/foo')

    @raises(NotImplementedError)
    def test_create_on_file(self):
        self.fsbase.create_on_file('myimage')

    @patch('kiwi.filesystem_base.Command.run')
    def test_is_mounted_true(self, mock_command):
        self.fsbase.mountpoint = 'tmpdir'
        assert self.fsbase.is_mounted()
        mock_command.assert_called_once_with(['mountpoint', 'tmpdir'])
        self.fsbase.mountpoint = None

    @patch('kiwi.filesystem_base.Command.run')
    def test_is_mounted_false(self, mock_command):
        mock_command.side_effect = Exception
        self.fsbase.mountpoint = 'tmpdir'
        assert self.fsbase.is_mounted() is False
        self.fsbase.mountpoint = None

    @patch('kiwi.filesystem_base.Command.run')
    @patch('kiwi.filesystem_base.DataSync')
    @patch('kiwi.filesystem_base.FileSystemBase.is_mounted')
    @patch('kiwi.filesystem_base.mkdtemp')
    @patch('os.path.exists')
    def test_sync_data(
        self, mock_exists, mock_mkdtemp, mock_mounted, mock_sync, mock_command
    ):
        data_sync = mock.Mock()
        mock_sync.return_value = data_sync
        mock_exists.return_value = True
        mock_mkdtemp.return_value = 'tmpdir'
        self.fsbase.sync_data(['exclude_me'])
        mock_sync.assert_called_once_with('root_dir', 'tmpdir')
        data_sync.sync_data.assert_called_once_with(['exclude_me'])
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'mount', '/dev/loop0', 'tmpdir'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'umount', 'tmpdir'
            ])
        call = mock_command.call_args_list[2]
        assert mock_command.call_args_list[2] == \
            call([
                'rmdir', 'tmpdir'
            ])

    @patch('kiwi.filesystem_base.Command.run')
    @patch('kiwi.filesystem_base.FileSystemBase.is_mounted')
    def test_destructor_valid_mountpoint(self, mock_mounted, mock_command):
        mock_mounted.return_value = True
        self.fsbase.mountpoint = 'tmpdir'
        self.fsbase.__del__()
        self.fsbase.mountpoint = None
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['umount', 'tmpdir'])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call(['rmdir', 'tmpdir'])

    @patch('kiwi.filesystem_base.Command.run')
    @patch('kiwi.filesystem_base.FileSystemBase.is_mounted')
    @patch('kiwi.logger.log.warning')
    @patch('time.sleep')
    def test_destructor_mountpoint_busy(
        self, mock_sleep, mock_warn, mock_mounted, mock_command
    ):
        mock_command.side_effect = Exception
        mock_mounted.return_value = True
        self.fsbase.mountpoint = 'tmpdir'
        self.fsbase.__del__()
        self.fsbase.mountpoint = None
        assert mock_warn.called
