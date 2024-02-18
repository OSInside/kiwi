import sys
import logging
from unittest.mock import (
    patch, call, Mock
)
from pytest import (
    raises, fixture
)

from ..test_helper import argv_kiwi_tests

from kiwi.system.root_bind import RootBind

from kiwi.exceptions import (
    KiwiMountKernelFileSystemsError,
    KiwiMountSharedDirectoryError,
    KiwiSetupIntermediateConfigError
)


class TestRootBind:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        root = Mock()
        root.root_dir = 'root-dir'
        self.bind_root = RootBind(root)

        # stub config files and bind locations
        self.bind_root.config_files = ['/etc/sysconfig/proxy']
        self.bind_root.bind_locations = ['/proc']

        # stub files/dirs and mountpoints to cleanup
        self.mount_manager = Mock()
        self.bind_root.cleanup_files = ['/etc/sysconfig/proxy.kiwi']
        self.bind_root.mount_stack = [self.mount_manager]
        self.bind_root.dir_stack = ['/mountpoint']

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

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
        with raises(KiwiMountKernelFileSystemsError):
            self.bind_root.mount_kernel_file_systems()
        mock_cleanup.assert_called_once_with()

    @patch('kiwi.system.root_bind.MountManager.bind_mount')
    @patch('kiwi.system.root_bind.Path.create')
    @patch('kiwi.system.root_bind.RootBind.cleanup')
    def test_shared_directory_raises_error(
        self, mock_cleanup, mock_path, mock_mount
    ):
        mock_mount.side_effect = KiwiMountSharedDirectoryError(
            'mount-error'
        )
        with raises(KiwiMountSharedDirectoryError):
            self.bind_root.mount_shared_directory()
        mock_cleanup.assert_called_once_with()

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
        with raises(KiwiSetupIntermediateConfigError):
            self.bind_root.setup_intermediate_config()
        mock_cleanup.assert_called_once_with()

    @patch('kiwi.system.root_bind.os.path.exists')
    @patch('kiwi.system.root_bind.MountManager')
    def test_mount_kernel_file_systems(self, mock_mount, mock_exists):
        mock_exists.return_value = True
        shared_mount = Mock()
        mock_mount.return_value = shared_mount
        assert self.bind_root.mount_kernel_file_systems() is None
        assert mock_mount.call_args_list == [
            call(device='root-dir', mountpoint='root-dir'),
            call(device='/proc', mountpoint='root-dir/proc')
        ]
        assert shared_mount.bind_mount.call_args_list == [
            call(), call()
        ]

    @patch('kiwi.system.root_bind.MountManager')
    def test_umount_kernel_file_systems(self, mock_mount):
        self.mount_manager.device = '/proc'
        self.mount_manager.is_mounted = Mock(return_value=True)
        assert self.bind_root.umount_kernel_file_systems() is None
        self.mount_manager.umount_lazy.assert_called_once_with()
        assert self.bind_root.mount_stack == []

    @patch('kiwi.system.root_bind.MountManager')
    def test_umount_kernel_file_systems_raises_error(self, mock_mount):
        self.mount_manager.device = '/proc'
        self.mount_manager.is_mounted = Mock(return_value=True)
        self.mount_manager.umount_lazy = Mock(side_effect=Exception)
        assert self.bind_root.umount_kernel_file_systems() is None
        self.mount_manager.umount_lazy.assert_called_once_with()
        assert self.bind_root.mount_stack == [self.mount_manager]

    @patch('kiwi.system.root_bind.MountManager')
    @patch('kiwi.system.root_bind.Path.create')
    def test_mount_shared_directory(self, mock_path, mock_mount):
        shared_mount = Mock()
        mock_mount.return_value = shared_mount
        assert self.bind_root.mount_shared_directory() is None
        mock_path.call_args_list = [
            call('root-dir/var/cache/kiwi'),
            call('/var/cache/kiwi')
        ]
        mock_mount.assert_called_once_with(
            device='/var/cache/kiwi', mountpoint='root-dir/var/cache/kiwi'
        )
        shared_mount.bind_mount.assert_called_once_with()

    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_bind.Checksum')
    @patch('os.path.exists')
    def test_intermediate_config(
        self, mock_exists, mock_Checksum, mock_command
    ):
        checksum = Mock()
        mock_Checksum.return_value = checksum
        mock_exists.return_value = True

        with patch('builtins.open') as m_open:
            assert self.bind_root.setup_intermediate_config() is None
            m_open.assert_called_once_with(
                'root-dir/etc/sysconfig/proxy.sha', 'w'
            )

        assert mock_command.call_args_list == [
            call([
                'cp', '/etc/sysconfig/proxy', 'root-dir/etc/sysconfig/proxy.kiwi'
            ]),
            call([
                'ln', '-s', '-f', 'proxy.kiwi', 'root-dir/etc/sysconfig/proxy'
            ])
        ]
        checksum.sha256.assert_called_once_with()

    @patch('textwrap.dedent')
    @patch('kiwi.system.root_bind.Checksum')
    @patch('kiwi.system.root_bind.MountManager.is_mounted')
    @patch('kiwi.system.root_bind.Command.run')
    @patch('kiwi.system.root_bind.Path.remove_hierarchy')
    @patch('os.path.islink')
    @patch('os.path.exists')
    @patch('shutil.move')
    def test_cleanup(
        self, mock_move, mock_exists, mock_islink,
        mock_remove_hierarchy, mock_command, mock_is_mounted,
        mock_Checksum, mock_dedent
    ):
        checksum = Mock()
        checksum.matches.return_value = False
        mock_Checksum.return_value = checksum
        os_exists_return_values = [False, True, True, False]

        def exists_side_effect(*args):
            return os_exists_return_values.pop()

        mock_is_mounted.return_value = False
        mock_exists.side_effect = exists_side_effect
        mock_islink.return_value = True
        with self._caplog.at_level(logging.WARNING):
            assert self.bind_root.cleanup() is None
            self.mount_manager.umount_lazy.assert_called_once_with()
            mock_remove_hierarchy.assert_called_once_with(
                root='root-dir', path='/mountpoint'
            )
            assert mock_command.call_args_list == [
                call(['rm', '-f', 'root-dir/etc/sysconfig/proxy']),
                call(
                    [
                        'cp',
                        'root-dir/usr/share/fillup-templates/sysconfig.proxy',
                        'root-dir/etc/sysconfig/proxy'
                    ]
                ),
                call(
                    [
                        'rm', '-f', 'root-dir/etc/sysconfig/proxy.kiwi',
                        'root-dir/etc/sysconfig/proxy.sha'
                    ]
                )
            ]
            mock_move.assert_called_once_with(
                'root-dir/etc/sysconfig/proxy.rpmnew',
                'root-dir/etc/sysconfig/proxy'
            )

    @patch('os.path.islink')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_bind.Path.remove_hierarchy')
    @patch('kiwi.system.root_bind.Checksum')
    def test_cleanup_continue_on_error(
        self, mock_Checksum, mock_remove_hierarchy,
        mock_command, mock_islink
    ):
        mock_islink.return_value = True
        mock_remove_hierarchy.side_effect = Exception('rm')
        mock_command.side_effect = Exception
        self.mount_manager.umount_lazy.side_effect = Exception
        with self._caplog.at_level(logging.WARNING):
            self.bind_root.cleanup()
            assert 'Image root directory root-dir not cleanly umounted:' in \
                self._caplog.text
            assert 'Failed to remove directory hierarchy '
            'root-dir/mountpoint: rm' in self._caplog.text
            assert 'Failed to cleanup intermediate config files' in \
                self._caplog.text

    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_bind.Path.remove_hierarchy')
    @patch('kiwi.system.root_bind.Checksum')
    def test_cleanup_nothing_mounted(
        self, mock_Checksum, mock_remove_hierarchy, mock_command
    ):
        self.mount_manager.is_mounted.return_value = False
        self.mount_manager.mountpoint = '/mountpoint'
        with self._caplog.at_level(logging.WARNING):
            assert self.bind_root.cleanup() is None
            assert 'Path /mountpoint not a mountpoint' in self._caplog.text
