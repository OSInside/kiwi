
from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import KiwiFileSystemSyncError
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
    @patch('os.path.exists')
    def test_sync_data(self, mock_exists, mock_sync, mock_mount):
        mock_exists.return_value = True

        filesystem_mount = mock.Mock()
        filesystem_mount.mountpoint = 'tmpdir'
        mock_mount.return_value = filesystem_mount

        data_sync = mock.Mock()
        mock_sync.return_value = data_sync

        self.fsbase.sync_data(['exclude_me'])

        mock_sync.assert_called_once_with('root_dir', 'tmpdir')
        data_sync.sync_data.assert_called_once_with(
            exclude=['exclude_me'],
            options=['-a', '-H', '-X', '-A', '--one-file-system']
        )
        mock_mount.assert_called_once_with(
            device='/dev/loop0'
        )
        filesystem_mount.mount.assert_called_once_with([])
        filesystem_mount.umount.assert_called_once_with()

    def test_destructor_valid_mountpoint(self):
        self.fsbase.filesystem_mount = mock.Mock()
        self.fsbase.__del__()
        self.fsbase.filesystem_mount.umount.assert_called_once_with()
