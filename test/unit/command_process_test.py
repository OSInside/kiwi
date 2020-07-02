import mock
import logging
from mock import patch
from pytest import (
    raises, fixture
)
from builtins import bytes

from kiwi.command_process import CommandProcess
from kiwi.command_process import CommandIterator

from kiwi.exceptions import KiwiCommandError


class TestCommandProcess:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def fake_matcher(self, item, output):
        return True

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
        self.data_flow = [True, None, None, None, None, None, None]
        self.data_out = [
            bytes(b''), bytes(b'\n'), bytes(b'a'),
            bytes(b't'), bytes(b'a'), bytes(b'd')
        ]
        self.data_err = [
            bytes(b''), bytes(b'r'), bytes(b'o'),
            bytes(b'r'), bytes(b'r'), bytes(b'e')
        ]
        self.flow = self.create_flow_method(self.poll)
        self.flow_out_available = self.create_flow_method(self.outavailable)
        self.flow_err_available = self.create_flow_method(self.erravailable)
        self.flow_out = self.create_flow_method(self.outdata)
        self.flow_err = self.create_flow_method(self.errdata)

    @patch('kiwi.command.Command')
    def test_returncode(self, mock_command):
        command = mock.Mock()
        mock_command.return_value = command
        process = CommandProcess(command)
        assert process.returncode() == command.process.returncode

    @patch('kiwi.command.Command')
    def test_poll_show_progress(self, mock_command):
        match_method = CommandProcess(mock_command).create_match_method(
            self.fake_matcher
        )
        process = CommandProcess(mock_command)
        process.command.command.process.poll = self.flow
        process.command.command.output_available = self.flow_out_available
        process.command.command.error_available = self.flow_err_available
        process.command.command.output.read = self.flow_out
        process.command.command.error.read = self.flow_err
        process.command.command.process.returncode = 0
        with self._caplog.at_level(logging.DEBUG):
            process.poll_show_progress(['a', 'b'], match_method)
            assert 'system: data' in self._caplog.text

    @patch('kiwi.command.Command')
    def test_poll_show_progress_raises(self, mock_command):
        match_method = CommandProcess(mock_command).create_match_method(
            self.fake_matcher
        )
        process = CommandProcess(mock_command)
        process.command.command.process.poll = self.flow
        process.command.command.output_available = self.flow_out_available
        process.command.command.error_available = self.flow_err_available
        process.command.command.output.read = self.flow_out
        process.command.command.error.read = self.flow_err
        process.command.command.process.returncode = 1
        with raises(KiwiCommandError):
            process.poll_show_progress(['a', 'b'], match_method)

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
            assert result.stderr == 'error'

    @patch('kiwi.command.Command')
    def test_create_match_method(self, mock_command):
        match_method = CommandProcess(mock_command).create_match_method(
            self.fake_matcher
        )
        assert match_method('a', 'b') is True

    @patch('kiwi.command.Command')
    def test_destructor(self, mock_command):
        process = CommandProcess(mock_command)
        process.command.command.process.returncode = None
        process.command.command.process.pid = 42
        process.command.command.process.kill = mock.Mock()
        process.__del__()
        process.command.command.process.kill.assert_called_once_with()

    def test_command_iterator(self):
        iterator = CommandIterator(mock.Mock())
        assert iterator.__iter__() == iterator
