from mock import patch
from pytest import raises
import mock

from kiwi.filesystem.base import FileSystemBase

from kiwi.exceptions import KiwiFileSystemSyncError


class TestFileSystemBase:
    def setup(self):
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/loop0'
        )
        custom_args = {
            'fs_attributes': ['no-copy-on-write']
        }
        self.fsbase = FileSystemBase(provider, 'root_dir', custom_args)

    def test_root_dir_does_not_exist(self):
        fsbase = FileSystemBase(mock.Mock(), 'root_dir_not_existing')
        with raises(KiwiFileSystemSyncError):
            fsbase.sync_data()

    def test_root_dir_not_defined(self):
        fsbase = FileSystemBase(mock.Mock())
        with raises(KiwiFileSystemSyncError):
            fsbase.sync_data()

    def test_create_on_device(self):
        with raises(NotImplementedError):
            self.fsbase.create_on_device('/dev/foo')

    def test_create_on_file(self):
        with raises(NotImplementedError):
            self.fsbase.create_on_file('myimage')

    def test_get_mountpoint(self):
        assert self.fsbase.get_mountpoint() is None

    @patch('kiwi.filesystem.base.MountManager')
    @patch('kiwi.filesystem.base.DataSync')
    @patch('kiwi.filesystem.base.Command.run')
    @patch('os.path.exists')
    def test_sync_data(
        self, mock_exists, mock_Command_run, mock_sync, mock_mount
    ):
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
            options=['-a', '-H', '-X', '-A', '--one-file-system', '--inplace']
        )
        mock_mount.assert_called_once_with(
            device='/dev/loop0'
        )
        mock_Command_run.assert_called_once_with(
            ['chattr', '+C', 'tmpdir']
        )
        filesystem_mount.mount.assert_called_once_with([])
        assert self.fsbase.get_mountpoint() == 'tmpdir'

    def test_umount(self):
        mount = mock.Mock()
        self.fsbase.filesystem_mount = mount
        self.fsbase.umount()
        mount.umount.assert_called_once_with()

    def test_destructor_valid_mountpoint(self):
        self.fsbase.filesystem_mount = mock.Mock()
        self.fsbase.__del__()
        assert self.fsbase.filesystem_mount is None
