from mock import patch
from mock import call
import mock

from .test_helper import raises

from kiwi.exceptions import (
    KiwiMountKernelFileSystemsError,
    KiwiMountSharedDirectoryError,
    KiwiSetupIntermediateConfigError
)

from kiwi.system.root_bind import RootBind


class TestRootBind(object):
    def setup(self):
        root = mock.Mock()
        root.root_dir = 'root-dir'
        self.bind_root = RootBind(root)

        # stub config files and bind locations
        self.bind_root.config_files = ['/foo']
        self.bind_root.bind_locations = ['/proc']

        # stub files/dirs and mountpoints to cleanup
        self.mount_manager = mock.Mock()
        self.bind_root.cleanup_files = ['/foo.kiwi']
        self.bind_root.mount_stack = [self.mount_manager]
        self.bind_root.dir_stack = ['/mountpoint']

    @raises(KiwiMountKernelFileSystemsError)
    @patch('kiwi.system.root_bind.MountManager.bind_mount')
    @patch('kiwi.system.root_bind.RootBind.cleanup')
    @patch('os.path.exists')
    def test_kernel_file_systems_raises_error(
        self, mock_exists, mock_cleanup, mock_mount
    ):
        mock_exists.return_value = True
        mock_mount.side_effect = KiwiMountKernelFileSystemsError(
            'mount-error'
        )
        self.bind_root.mount_kernel_file_systems()
        mock.cleanup.assert_called_once_with()

    @raises(KiwiMountSharedDirectoryError)
    @patch('kiwi.system.root_bind.MountManager.bind_mount')
    @patch('kiwi.system.root_bind.Path.create')
    @patch('kiwi.system.root_bind.RootBind.cleanup')
    def test_shared_directory_raises_error(
        self, mock_cleanup, mock_path, mock_mount
    ):
        mock_mount.side_effect = KiwiMountSharedDirectoryError(
            'mount-error'
        )
        self.bind_root.mount_shared_directory()
        mock.cleanup.assert_called_once_with()

    @raises(KiwiSetupIntermediateConfigError)
    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_bind.RootBind.cleanup')
    @patch('os.path.exists')
    def test_intermediate_config_raises_error(
        self, mock_exists, mock_cleanup, mock_command
    ):
        mock_exists.return_value = True
        mock_command.side_effect = KiwiSetupIntermediateConfigError(
            'config-error'
        )
        self.bind_root.setup_intermediate_config()
        mock.cleanup.assert_called_once_with()

    @patch('kiwi.system.root_bind.os.path.exists')
    @patch('kiwi.system.root_bind.MountManager')
    def test_mount_kernel_file_systems(self, mock_mount, mock_exists):
        mock_exists.return_value = True
        shared_mount = mock.Mock()
        mock_mount.return_value = shared_mount
        self.bind_root.mount_kernel_file_systems()
        mock_mount.assert_called_once_with(
            device='/proc', mountpoint='root-dir/proc'
        )
        shared_mount.bind_mount.assert_called_once_with()

    @patch('kiwi.system.root_bind.MountManager')
    @patch('kiwi.system.root_bind.Path.create')
    def test_mount_shared_directory(self, mock_path, mock_mount):
        shared_mount = mock.Mock()
        mock_mount.return_value = shared_mount
        self.bind_root.mount_shared_directory()
        mock_path.call_args_list = [
            call('root-dir/var/cache/kiwi'),
            call('/var/cache/kiwi')
        ]
        mock_mount.assert_called_once_with(
            device='/var/cache/kiwi', mountpoint='root-dir/var/cache/kiwi'
        )
        shared_mount.bind_mount.assert_called_once_with()

    @patch('kiwi.command.Command.run')
    @patch('os.path.exists')
    def test_intermediate_config(self, mock_exists, mock_command):
        mock_exists.return_value = True
        self.bind_root.setup_intermediate_config()
        assert mock_command.call_args_list == [
            call([
                'cp', '/foo', 'root-dir/foo.kiwi'
            ]),
            call([
                'ln', '-s', '-f', 'foo.kiwi', 'root-dir/foo'
            ])
        ]

    @patch('kiwi.system.root_bind.MountManager.is_mounted')
    @patch('kiwi.system.root_bind.Command.run')
    @patch('kiwi.system.root_bind.Path.remove_hierarchy')
    @patch('os.path.islink')
    @patch('os.path.exists')
    @patch('shutil.move')
    def test_cleanup(
        self, mock_move, mock_exists, mock_islink, mock_remove_hierarchy,
        mock_command, mock_is_mounted
    ):
        os_exists_return_values = [False, True]

        def exists_side_effect(*args):
            return os_exists_return_values.pop()

        mock_is_mounted.return_value = False
        mock_exists.side_effect = exists_side_effect
        mock_islink.return_value = True
        self.bind_root.cleanup()
        self.mount_manager.umount_lazy.assert_called_once_with()
        mock_remove_hierarchy.assert_called_once_with('root-dir/mountpoint')
        mock_command.assert_called_once_with(
            ['rm', '-f', 'root-dir/foo.kiwi', 'root-dir/foo']
        )
        mock_move.assert_called_once_with(
            'root-dir/foo.rpmnew', 'root-dir/foo'
        )

    @patch('os.path.islink')
    @patch('kiwi.logger.log.warning')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_bind.Path.remove_hierarchy')
    def test_cleanup_continue_on_error(
        self, mock_remove_hierarchy, mock_command, mock_warn, mock_islink
    ):
        mock_islink.return_value = True
        mock_remove_hierarchy.side_effect = Exception('rm')
        mock_command.side_effect = Exception
        self.mount_manager.umount_lazy.side_effect = Exception
        self.bind_root.cleanup()
        assert mock_warn.call_args_list == [
            call(
                'Image root directory %s not cleanly umounted: %s',
                'root-dir', ''
            ),
            call(
                'Failed to remove directory hierarchy root-dir/mountpoint: rm'
            ),
            call(
                'Failed to remove intermediate config files: %s', ''
            )
        ]

    @patch('kiwi.logger.log.warning')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_bind.Path.remove_hierarchy')
    def test_cleanup_nothing_mounted(
        self, mock_remove_hierarchy, mock_command, mock_warn
    ):
        self.mount_manager.is_mounted.return_value = False
        self.mount_manager.mountpoint = '/mountpoint'
        self.bind_root.cleanup()
        mock_warn.assert_called_once_with(
            'Path %s not a mountpoint', '/mountpoint'
        )

    def test_move_to_root(self):
        assert self.bind_root.move_to_root(
            [self.bind_root.root_dir + '/argument']
        ) == ['/argument']
