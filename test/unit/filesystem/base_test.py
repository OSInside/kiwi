from mock import patch
from pytest import raises
import mock

import kiwi.defaults as defaults

from kiwi.filesystem.base import FileSystemBase

from kiwi.exceptions import KiwiFileSystemSyncError


class TestFileSystemBase:
    def setup(self):
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/loop0'
        )
        provider.get_byte_size = mock.Mock(
            return_value=1073741824  # 1GB
        )
        custom_args = {
            'fs_attributes': ['no-copy-on-write']
        }
        self.fsbase = FileSystemBase(provider, 'root_dir', custom_args)

    def setup_method(self, cls):
        self.setup()

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
            options=[
                '--archive', '--hard-links', '--xattrs',
                '--acls', '--one-file-system', '--inplace'
            ]
        )
        mock_mount.assert_called_once_with(
            device='/dev/loop0'
        )
        mock_Command_run.assert_called_once_with(
            ['chattr', '+C', 'tmpdir']
        )
        filesystem_mount.mount.assert_called_once_with([])
        assert self.fsbase.get_mountpoint() == 'tmpdir'

    @patch('kiwi.filesystem.base.VeritySetup')
    def test_create_verity_layer(self, mock_VeritySetup):
        self.fsbase.create_verity_layer()
        mock_VeritySetup.return_value.format.assert_called_once_with()

    def test_create_verification_metadata(self):
        veritysetup = mock.Mock()
        self.fsbase.veritysetup = veritysetup
        self.fsbase.create_verification_metadata('/some/device')
        veritysetup.create_verity_verification_metadata.assert_called_once_with()
        veritysetup.sign_verification_metadata.assert_called_once_with()
        veritysetup.write_verification_metadata.assert_called_once_with(
            '/some/device'
        )

    def test_umount(self):
        mount = mock.Mock()
        self.fsbase.filesystem_mount = mount
        self.fsbase.umount()
        mount.umount.assert_called_once_with()

    def test_fs_size(self):
        # size of 100k must be 100k (default unit)
        assert self.fsbase._fs_size(100) == '100'
        # size of 1073741824b (see test init) - 100k must be 1048476k
        assert self.fsbase._fs_size(-100) == '1048476'
        # size of 1073741824b (see test init) - 102400b must be 1073639424b
        assert self.fsbase._fs_size(
            -102400, unit=defaults.UNIT.byte
        ) == '1073639424'
        # size of 1073741824b - 1024m must be zero
        assert self.fsbase._fs_size(-1024, unit=defaults.UNIT.mb) == '0'
        # size of 1073741824b - 1g must be zero
        assert self.fsbase._fs_size(-1, unit=defaults.UNIT.gb) == '0'

    def test_destructor_valid_mountpoint(self):
        self.fsbase.filesystem_mount = mock.Mock()
        self.fsbase.__del__()
        assert self.fsbase.filesystem_mount is None
