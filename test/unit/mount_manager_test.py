import logging
from pytest import (
    fixture, raises
)
from mock import (
    patch, call, Mock
)
from kiwi.exceptions import KiwiUmountBusyError
from kiwi.mount_manager import MountManager


class TestMountManager:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.mount_manager.Path.create')
    def setup(self, mock_path_create):
        self.mount_manager = MountManager(
            '/dev/some-device', '/some/mountpoint'
        )
        mock_path_create.assert_called_once_with('/some/mountpoint')

    @patch('kiwi.mount_manager.Path.create')
    def setup_method(self, cls, mock_path_create):
        self.setup()

    @patch('kiwi.mount_manager.Temporary')
    def test_setup_empty_mountpoint(self, mock_Temporary):
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        mount_manager = MountManager('/dev/some-device')
        assert mount_manager.mountpoint == 'tmpdir'

    @patch('kiwi.mount_manager.Command.run')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    def test_bind_mount(self, mock_mounted, mock_command):
        mock_mounted.return_value = False
        self.mount_manager.bind_mount()
        mock_command.assert_called_once_with(
            ['mount', '-n', '--bind', '/dev/some-device', '/some/mountpoint']
        )

    @patch('kiwi.mount_manager.Command.run')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    def test_tmpfs_mount(self, mock_mounted, mock_command):
        mock_mounted.return_value = False
        self.mount_manager.tmpfs_mount()
        mock_command.assert_called_once_with(
            ['mount', '-t', 'tmpfs', 'tmpfs', '/some/mountpoint']
        )

    @patch('kiwi.mount_manager.Command.run')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    def test_mount(self, mock_mounted, mock_command):
        mock_mounted.return_value = False
        self.mount_manager.mount(['options'])
        mock_command.assert_called_once_with(
            ['mount', '-o', 'options', '/dev/some-device', '/some/mountpoint']
        )

    @patch('kiwi.mount_manager.Command.run')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    def test_umount_lazy(self, mock_mounted, mock_command):
        mock_mounted.return_value = True
        self.mount_manager.umount_lazy()
        mock_command.assert_called_once_with(
            ['umount', '-l', '/some/mountpoint']
        )

    @patch('kiwi.mount_manager.Command.run')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    @patch('time.sleep')
    def test_umount_with_errors(
        self, mock_sleep, mock_mounted, mock_command
    ):
        mock_command.side_effect = Exception
        mock_mounted.return_value = True
        with self._caplog.at_level(logging.WARNING):
            assert self.mount_manager.umount(raise_on_busy=False) is False
        assert mock_command.call_args_list == [
            call(['umount', '/some/mountpoint']),  # 1
            call(['umount', '/some/mountpoint']),  # 2
            call(['umount', '/some/mountpoint']),  # 3
            call(['umount', '/some/mountpoint']),  # 4
            call(['umount', '/some/mountpoint']),  # 5
            call(['umount', '/some/mountpoint']),  # 6
            call(['umount', '/some/mountpoint']),  # 7
            call(['umount', '/some/mountpoint']),  # 8
            call(['umount', '/some/mountpoint']),  # 9
            call(['umount', '/some/mountpoint'])   # 10
        ]

    @patch('kiwi.mount_manager.Command.run')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    @patch('time.sleep')
    @patch('kiwi.mount_manager.Path.which')
    def test_umount_with_errors_raises_no_lsof_present(
        self, mock_Path_which, mock_sleep, mock_mounted, mock_command
    ):
        def command_call(args):
            if 'umount' in args:
                raise Exception

        mock_Path_which.return_value = None
        mock_command.side_effect = command_call
        mock_mounted.return_value = True
        with raises(KiwiUmountBusyError):
            self.mount_manager.umount()

    @patch('kiwi.mount_manager.Command.run')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    @patch('time.sleep')
    @patch('kiwi.mount_manager.Path.which')
    def test_umount_with_errors_raises_lsof_present(
        self, mock_Path_which, mock_sleep, mock_mounted, mock_command
    ):
        def command_call(args, raise_on_error=None):
            if 'umount' in args:
                raise Exception
            else:
                call_return = Mock()
                call_return.output = 'HEADLINE\ndata'
                return call_return

        mock_Path_which.return_value = 'lsof'
        mock_command.side_effect = command_call
        mock_mounted.return_value = True
        with raises(KiwiUmountBusyError) as issue:
            self.mount_manager.umount()
        assert 'HEADLINE' in issue.value.message

    @patch('kiwi.mount_manager.Command.run')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    def test_umount_success(self, mock_mounted, mock_command):
        mock_mounted.return_value = True
        assert self.mount_manager.umount() is True
        mock_command.assert_called_once_with(
            ['umount', '/some/mountpoint']
        )

    @patch('kiwi.mount_manager.Command.run')
    def test_is_mounted_true(self, mock_command):
        command = Mock()
        command.returncode = 0
        mock_command.return_value = command
        assert self.mount_manager.is_mounted() is True
        mock_command.assert_called_once_with(
            command=['mountpoint', '-q', '/some/mountpoint'],
            raise_on_error=False
        )

    @patch('kiwi.mount_manager.Command.run')
    def test_is_mounted_false(self, mock_command):
        command = Mock()
        command.returncode = 1
        mock_command.return_value = command
        assert self.mount_manager.is_mounted() is False
        mock_command.assert_called_once_with(
            command=['mountpoint', '-q', '/some/mountpoint'],
            raise_on_error=False
        )
