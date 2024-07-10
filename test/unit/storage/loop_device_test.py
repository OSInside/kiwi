import logging
from unittest.mock import (
    patch, call
)
from pytest import (
    raises, fixture
)

from kiwi.storage.loop_device import LoopDevice

from kiwi.exceptions import (
    KiwiLoopSetupError,
    KiwiCommandError
)


class TestLoopDevice:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = False
        self.loop = LoopDevice('loop-file', 20, 4096)

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    def test_loop_setup_invalid(self):
        with raises(KiwiLoopSetupError):
            LoopDevice('loop-file-does-not-exist-and-no-size-given')

    def test_get_device(self):
        assert self.loop.get_device() == ''

    def test_is_loop(self):
        assert self.loop.is_loop() is True

    @patch('os.path.exists')
    @patch('kiwi.storage.loop_device.Command.run')
    @patch('kiwi.storage.loop_device.CommandCapabilities.has_option_in_help')
    def test_create(
        self, mock_has_option_in_help, mock_command, mock_exists
    ):
        mock_has_option_in_help.return_value = True
        mock_exists.return_value = False
        self.loop.create()
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'qemu-img', 'create', 'loop-file', '20M'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'losetup', '--sector-size', '4096',
                '-f', '--show', 'loop-file'
            ])
        mock_has_option_in_help.return_value = False
        mock_command.reset_mock()
        self.loop.create()
        assert mock_command.call_args_list[1] == \
            call([
                'losetup', '--logical-blocksize', '4096',
                '-f', '--show', 'loop-file'
            ])
        self.loop.node_name = None

    @patch('kiwi.storage.loop_device.Command.run')
    @patch('os.path.exists')
    @patch('pathlib.Path.is_block_device')
    @patch('time.sleep')
    def test_context_manager_exit_loop_released(
        self, mock_time_sleep, mock_is_block_device,
        mock_os_path_exists, mock_command_run
    ):
        is_block_device = [False, True]
        mock_os_path_exists.return_value = True
        mock_command_run.side_effect = KiwiCommandError('error')

        def Command_run(params):
            # raise on first command which is 'losetup -f ...'
            if params[1] == '-f':
                raise KiwiCommandError('issue')

        def Path_is_block_device():
            return is_block_device.pop()

        mock_is_block_device.side_effect = Path_is_block_device
        mock_command_run.side_effect = Command_run

        with self._caplog.at_level(logging.ERROR):
            with LoopDevice('loop-file', 20) as loop_provider:
                loop_provider.node_name = '/dev/loop0'
                with raises(KiwiCommandError):
                    loop_provider.create(overwrite=False)
            assert len(mock_is_block_device.call_args_list) == 2
            assert mock_command_run.call_args_list == [
                call(['losetup', '-f', '--show', 'loop-file']),
                call(['losetup', '-d', '/dev/loop0'])
            ]

    @patch('kiwi.storage.loop_device.Command.run')
    @patch('os.path.exists')
    @patch('pathlib.Path.is_block_device')
    @patch('time.sleep')
    def test_context_manager_exit_loop_not_released(
        self, mock_time_sleep, mock_is_block_device,
        mock_os_path_exists, mock_command_run
    ):
        mock_os_path_exists.return_value = True
        mock_command_run.side_effect = KiwiCommandError('error')
        mock_is_block_device.return_value = True

        def Command_run(params):
            # raise on first command which is 'losetup -f ...'
            if params[1] == '-f':
                raise KiwiCommandError('issue')

        mock_command_run.side_effect = Command_run

        with self._caplog.at_level(logging.ERROR):
            with LoopDevice('loop-file', 20) as loop_provider:
                loop_provider.node_name = '/dev/loop0'
                with raises(KiwiCommandError):
                    loop_provider.create(overwrite=False)
            assert mock_command_run.call_args_list == [
                call(['losetup', '-f', '--show', 'loop-file']),
                call(['losetup', '-d', '/dev/loop0'])
            ]
