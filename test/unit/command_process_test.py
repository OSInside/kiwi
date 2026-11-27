import logging
from unittest.mock import patch, Mock, call
from pytest import raises, fixture
from builtins import bytes

from kiwi.command_process import CommandProcess, CommandIterator
from kiwi.logger_console import KiwiConsole
from kiwi.utils.install_progress import PackageManagerEventT

from kiwi.exceptions import KiwiCommandError


class TestCommandProcess:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def poll(self):
        return self.data_flow.pop()

    def outavailable(self):
        return True

    def erravailable(self):
        return True

    def outdata(self):
        return self.data_out.pop()

    def errdata(self):
        return self.data_err.pop()

    def create_flow_method(self, method):
        def create_method(arg=None):
            return method()

        return create_method

    def setup(self):
        self.data_flow = [True, None, None, None, None, None, None, None]
        self.data_out = [
            bytes(b''),
            bytes(b''),
            bytes(b'\n'),
            bytes(b'a'),
            bytes(b't'),
            bytes(b'a'),
            bytes(b'd'),
        ]
        self.data_err = [
            bytes(b''),
            bytes(b'\n'),
            bytes(b'r'),
            bytes(b'o'),
            bytes(b'r'),
            bytes(b'r'),
            bytes(b'e'),
        ]
        self.flow = self.create_flow_method(self.poll)
        self.flow_out_available = self.create_flow_method(self.outavailable)
        self.flow_err_available = self.create_flow_method(self.erravailable)
        self.flow_out = self.create_flow_method(self.outdata)
        self.flow_err = self.create_flow_method(self.errdata)

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.command.Command')
    def test_returncode(self, mock_command):
        command = Mock()
        mock_command.return_value = command
        process = CommandProcess(command)
        assert process.returncode() == command.process.returncode

    @patch('kiwi.command.Command')
    def test_poll_show_progress(self, mock_command):
        process = self._process(mock_command)
        with self._caplog.at_level(logging.DEBUG):
            process.poll_show_progress(lambda line: None, [], True)
            assert 'system: data' in self._caplog.text
            assert 'system: error' in self._caplog.text

    def _process(self, mock_command):
        process = CommandProcess(mock_command)
        process.command.command.process.poll = self.flow
        process.command.command.output_available = self.flow_out_available
        process.command.command.error_available = self.flow_err_available
        process.command.command.output.read = self.flow_out
        process.command.command.error.read = self.flow_err
        process.command.command.process.returncode = 0
        return process

    @patch('kiwi.command_process.Progress')
    @patch('kiwi.command.Command')
    def test_poll_show_progress_no_events(self, mock_command, mock_Progress):
        progress = mock_Progress.return_value.__enter__.return_value
        task = progress.add_task.return_value
        process = self._process(mock_command)
        with self._caplog.at_level(logging.INFO):
            process.poll_show_progress(lambda line: None, ['install'], True)
        # the progress is written to the console of the log messages
        # and replaced by the summary when done
        assert mock_Progress.call_args.kwargs == {
            'console': KiwiConsole.stdout,
            'transient': True,
            'disable': not KiwiConsole.stdout.is_terminal,
        }
        progress.add_task.assert_called_once_with('Processing', total=1000)
        # without progress events the progress is complete at the end
        assert progress.update.call_args_list == [call(task, completed=1000)]
        assert 'installed' not in self._caplog.text

    @patch('kiwi.command_process.Progress')
    @patch('kiwi.command.Command')
    def test_poll_show_progress_events(self, mock_command, mock_Progress):
        progress = mock_Progress.return_value.__enter__.return_value
        task = progress.add_task.return_value
        process = self._process(mock_command)
        events = {
            'data': PackageManagerEventT(
                phase='install',
                description='Installing data',
                current=1,
                total=2,
                package='data',
            ),
            'error': PackageManagerEventT(
                phase='script',
                description='Running %post(data)',
                package='%post(data)',
            ),
        }
        with self._caplog.at_level(logging.INFO):
            process.poll_show_progress(events.get, ['install'], True)
        assert progress.update.call_args_list == [
            call(task, description='1/2 Installing data', completed=500),
            call(task, description='Running %post(data)', completed=500),
            call(task, completed=1000),
        ]
        assert '1 package installed, 1 script run' in self._caplog.text

    @patch('kiwi.command.Command')
    def test_poll_show_progress_raises(self, mock_command):
        process = CommandProcess(mock_command)
        process.command.command.process.poll = self.flow
        process.command.command.output_available = self.flow_out_available
        process.command.command.error_available = self.flow_err_available
        process.command.command.output.read = self.flow_out
        process.command.command.error.read = self.flow_err
        process.command.command.process.returncode = 1
        with raises(KiwiCommandError):
            process.poll_show_progress(lambda line: None, [])

    @patch('kiwi.command.Command')
    def test_poll(self, mock_command):
        process = CommandProcess(mock_command)
        process.command.command.process.poll = self.flow
        process.command.command.output_available = self.flow_out_available
        process.command.command.error_available = self.flow_err_available
        process.command.command.output.read = self.flow_out
        process.command.command.error.read = self.flow_err
        process.command.command.process.returncode = 0
        with self._caplog.at_level(logging.DEBUG):
            process.poll()
            assert 'system: data' in self._caplog.text

    @patch('kiwi.command.Command')
    def test_poll_raises(self, mock_command):
        process = CommandProcess(mock_command)
        process.command.command.process.poll = self.flow
        process.command.command.output_available = self.flow_out_available
        process.command.command.error_available = self.flow_err_available
        process.command.command.output.read = self.flow_out
        process.command.command.error.read = self.flow_err
        process.command.command.output.read.return_value = 'data'
        process.command.command.process.returncode = 1
        with raises(KiwiCommandError):
            process.poll()

    @patch('kiwi.command.Command')
    def test_poll_and_watch(self, mock_command):
        process = CommandProcess(mock_command)
        process.command.command.process.poll = self.flow
        process.command.command.output_available = self.flow_out_available
        process.command.command.error_available = self.flow_err_available
        process.command.command.output.read = self.flow_out
        process.command.command.error.read = self.flow_err
        process.command.command.process.returncode = 1
        with self._caplog.at_level(logging.DEBUG):
            result = process.poll_and_watch()
            assert '--------------out start-------------' in self._caplog.text
            assert 'data' in self._caplog.text
            assert '--------------out stop--------------' in self._caplog.text
            assert result.stderr == 'error\n'

    def test_command_iterator(self):
        iterator = CommandIterator(Mock())
        assert iterator.__iter__() == iterator

    def test_kill(self):
        iterator = CommandIterator(Mock())
        iterator.kill()
        iterator.command.process.kill.assert_called_once_with()

    def test_get_pid(self):
        iterator = CommandIterator(Mock())
        assert iterator.get_pid() == iterator.command.process.pid
