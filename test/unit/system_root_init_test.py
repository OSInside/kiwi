from mock import patch
from mock import call
import mock

from .test_helper import raises

from kiwi.exceptions import (
    KiwiRootDirExists,
    KiwiRootInitCreationError
)

from kiwi.system.root_init import RootInit


class TestRootInit(object):
    @raises(KiwiRootDirExists)
    @patch('os.path.exists')
    def test_init_raises_error(self, mock_path):
        mock_path.return_value = True
        RootInit('root_dir')

    @raises(KiwiRootInitCreationError)
    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.chown')
    @patch('os.symlink')
    @patch('shutil.rmtree')
    @patch('kiwi.system.root_init.DataSync')
    @patch('kiwi.system.root_init.mkdtemp')
    @patch('kiwi.system.root_init.Command.run')
    def test_create_raises_error(
        self, mock_command, mock_temp, mock_data_sync, mock_rmtree,
        mock_symlink, mock_chwon, mock_makedirs, mock_path
    ):
        mock_path.return_value = False
        mock_temp.return_value = 'tmpdir'
        mock_data_sync.side_effect = Exception
        root = RootInit('root_dir')
        root.create()

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('os.chown')
    @patch('os.symlink')
    @patch('os.makedev')
    @patch('kiwi.system.root_init.copy')
    @patch('kiwi.system.root_init.rmtree')
    @patch('kiwi.system.root_init.DataSync')
    @patch('kiwi.system.root_init.mkdtemp')
    @patch('kiwi.system.root_init.Command.run')
    def test_create(
        self, mock_command, mock_temp, mock_data_sync, mock_rmtree, mock_copy,
        mock_makedev, mock_symlink, mock_chwon, mock_makedirs,
        mock_path
    ):
        data_sync = mock.Mock()
        mock_data_sync.return_value = data_sync
        mock_makedev.return_value = 'makedev'
        mock_path_return = [
            True, True, True, True, False, False, False, False, False, False, False
        ]

        def path_exists(self):
            return mock_path_return.pop()

        mock_path.side_effect = path_exists

        mock_path.return_value = False
        mock_temp.return_value = 'tmpdir'
        root = RootInit('root_dir', True)
        root.create()
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
            call('fd/1', 'tmpdir/dev/stdout'),
            call('/run', 'tmpdir/var/run')
        ]
        assert mock_command.call_args_list == [
            call(['mkdir', '-p', 'root_dir']),
            call([
                'cp',
                '/var/adm/fillup-templates/group.aaa_base',
                'tmpdir/etc/group'
            ]),
            call([
                'cp',
                '/var/adm/fillup-templates/passwd.aaa_base',
                'tmpdir/etc/passwd'
            ]),
            call([
                'cp',
                '/var/adm/fillup-templates/sysconfig.proxy',
                'tmpdir/etc/sysconfig/proxy'
            ])
        ]
        mock_data_sync.assert_called_once_with(
            'tmpdir/', 'root_dir'
        )
        data_sync.sync_data.assert_called_once_with(
            options=['-a', '--ignore-existing']
        )
        mock_rmtree.assert_called_once_with(
            'tmpdir', ignore_errors=True
        )

        mock_copy.assert_called_once_with(
            '/.buildenv', 'root_dir'
        )

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_delete(self, mock_path, mock_command):
        mock_path.return_value = False
        root = RootInit('root_dir')
        root.delete()
        mock_command.assert_called_once_with(
            ['rm', '-r', '-f', 'root_dir']
        )
