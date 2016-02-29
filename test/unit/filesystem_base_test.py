from nose.tools import *
from mock import patch

import mock

from . import nose_helper

from kiwi.exceptions import *
from kiwi.filesystem.base import FileSystemBase


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

    @patch('kiwi.filesystem.base.MountManager')
    @patch('kiwi.filesystem.base.DataSync')
    @patch('kiwi.filesystem.base.mkdtemp')
    @patch('os.path.exists')
    def test_sync_data(self, mock_exists, mock_mkdtemp, mock_sync, mock_mount):
        mock_mkdtemp.return_value = 'tmpdir'
        mock_exists.return_value = True

        filesystem_mount = mock.Mock()
        filesystem_mount.mountpoint = mock_mkdtemp.return_value
        mock_mount.return_value = filesystem_mount

        data_sync = mock.Mock()
        mock_sync.return_value = data_sync

        self.fsbase.sync_data(['exclude_me'])

        mock_sync.assert_called_once_with('root_dir', 'tmpdir')
        data_sync.sync_data.assert_called_once_with(['exclude_me'])
        mock_mount.assert_called_once_with(
            device='/dev/loop0', mountpoint='tmpdir'
        )
        filesystem_mount.mount.assert_called_once_with()
        filesystem_mount.umount.assert_called_once_with()

    def test_destructor_valid_mountpoint(self):
        self.fsbase.filesystem_mount = mock.Mock()
        self.fsbase.__del__()
        self.fsbase.filesystem_mount.umount.assert_called_once_with()
