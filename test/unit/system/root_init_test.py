import sys
from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from ..test_helper import argv_kiwi_tests

from kiwi.system.root_init import RootInit

from kiwi.exceptions import (
    KiwiRootDirExists,
    KiwiRootInitCreationError
)


class TestRootInit:
    @patch('os.path.exists')
    def test_init_raises_error(self, mock_path):
        mock_path.return_value = True
        with raises(KiwiRootDirExists):
            RootInit('root_dir')

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.chown')
    @patch('os.symlink')
    @patch('kiwi.system.root_init.DataSync')
    @patch('kiwi.system.root_init.Temporary')
    @patch('kiwi.system.root_init.Path.create')
    def test_create_raises_error(
        self, mock_Path_create, mock_Temporary, mock_data_sync,
        mock_symlink, mock_chwon, mock_makedirs, mock_path
    ):
        mock_path.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        mock_data_sync.side_effect = Exception
        root = RootInit('root_dir')
        with raises(KiwiRootInitCreationError):
            root.create()

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.chown')
    @patch('os.symlink')
    @patch('os.makedev')
    @patch('kiwi.path.Path.create')
    @patch('kiwi.system.root_init.copy')
    @patch('kiwi.system.root_init.DataSync')
    @patch('kiwi.system.root_init.Temporary')
    @patch('kiwi.system.root_init.Path.create')
    def test_create(
        self, mock_Path_create, mock_Temporary, mock_data_sync,
        mock_copy, mock_create, mock_makedev,
        mock_symlink, mock_chwon, mock_makedirs,
        mock_path
    ):
        data_sync = Mock()
        mock_data_sync.return_value = data_sync
        mock_makedev.return_value = 'makedev'
        mock_path_return = [
            True, True, True, True, False, False,
            False, False, False, False, False
        ]

        def path_exists(self):
            return mock_path_return.pop()

        mock_path.side_effect = path_exists

        mock_path.return_value = False
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        root = RootInit('root_dir', True)
        assert root.create() is None
        assert mock_makedirs.call_args_list == [
            call('tmpdir/var/cache/kiwi'),
            call('tmpdir/dev/pts'),
            call('tmpdir/proc'),
            call('tmpdir/etc/sysconfig'),
            call('tmpdir/run'),
            call('tmpdir/sys'),
            call('tmpdir/var')
        ]
        assert mock_chwon.call_args_list == [
            call('tmpdir/var/cache/kiwi', 0, 0),
            call('tmpdir/dev/pts', 0, 0),
            call('tmpdir/proc', 0, 0),
            call('tmpdir/etc/sysconfig', 0, 0),
            call('tmpdir/run', 0, 0),
            call('tmpdir/sys', 0, 0),
            call('tmpdir/var', 0, 0)
        ]
        assert mock_symlink.call_args_list == [
            call('/proc/self/fd', 'tmpdir/dev/fd'),
            call('fd/2', 'tmpdir/dev/stderr'),
            call('fd/0', 'tmpdir/dev/stdin'),
            call('fd/1', 'tmpdir/dev/stdout')
        ]
        mock_data_sync.assert_called_once_with(
            'tmpdir/', 'root_dir'
        )
        data_sync.sync_data.assert_called_once_with(
            options=['-a', '--ignore-existing']
        )

        mock_copy.assert_called_once_with(
            '/.buildenv', 'root_dir'
        )
        mock_create.assert_called_once_with('root_dir')

    @patch('kiwi.path.Path.wipe')
    @patch('os.path.exists')
    def test_delete(self, mock_path, mock_wipe):
        mock_path.return_value = False
        root = RootInit('root_dir')
        assert root.delete() is None
        mock_wipe.assert_called_once_with('root_dir')

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()
