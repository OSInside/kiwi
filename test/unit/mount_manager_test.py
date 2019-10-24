import logging
from pytest import fixture
from mock import (
    patch, call
)
import mock

from kiwi.mount_manager import MountManager


class TestMountManager:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.mount_manager = MountManager(
            '/dev/some-device', '/some/mountpoint'
        )

    @patch('kiwi.mount_manager.mkdtemp')
    def test_setup_empty_mountpoint(self, mock_mkdtemp):
        mock_mkdtemp.return_value = 'tmpdir'
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
            assert self.mount_manager.umount() is False
        assert mock_command.call_args_list == [
            call(['umount', '/some/mountpoint']),
            call(['umount', '/some/mountpoint']),
            call(['umount', '/some/mountpoint'])
        ]

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
        command = mock.Mock()
        command.returncode = 0
        mock_command.return_value = command
        assert self.mount_manager.is_mounted() is True
        mock_command.assert_called_once_with(
            command=['mountpoint', '-q', '/some/mountpoint'],
            raise_on_error=False
        )

    @patch('kiwi.mount_manager.Command.run')
    def test_is_mounted_false(self, mock_command):
        command = mock.Mock()
        command.returncode = 1
        mock_command.return_value = command
        assert self.mount_manager.is_mounted() is False
        mock_command.assert_called_once_with(
            command=['mountpoint', '-q', '/some/mountpoint'],
            raise_on_error=False
        )

    @patch('kiwi.mount_manager.Path.wipe')
    @patch('kiwi.mount_manager.MountManager.is_mounted')
    def test_destructor(self, mock_mounted, mock_wipe):
        self.mount_manager.mountpoint_created_by_mount_manager = True
        mock_mounted.return_value = False
        self.mount_manager.__del__()
        mock_wipe.assert_called_once_with('/some/mountpoint')
