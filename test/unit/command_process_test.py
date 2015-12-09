from nose.tools import *
from mock import patch
from mock import call
from collections import namedtuple

import mock

import nose_helper

from kiwi.exceptions import (
    KiwiCommandError
)
from kiwi.command_process import CommandProcess


class TestCommandProcess(object):
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
        self.data_flow = [True, None]
        self.data_out = ['', '\n', 'a', 't', 'a', 'd']
        self.data_err = ['', 'r', 'o', 'r', 'r', 'e']
        self.flow = self.create_flow_method(self.poll)
        self.flow_out_available = self.create_flow_method(self.outavailable)
        self.flow_err_available = self.create_flow_method(self.erravailable)
        self.flow_out = self.create_flow_method(self.outdata)
        self.flow_err = self.create_flow_method(self.errdata)

    @patch('kiwi.command.Command')
    @patch('kiwi.logger.log.debug')
    def test_poll_show_progress(self, mock_log_debug, mock_command):
        match_method = CommandProcess(None).create_match_method(
            self.fake_matcher
        )
        process = CommandProcess(mock_command)
        process.command.process.poll = self.flow
        process.command.output_available = self.flow_out_available
        process.command.error_available = self.flow_err_available
        process.command.output.read = self.flow_out
        process.command.error.read = self.flow_err
        process.command.process.returncode = 0
        process.poll_show_progress(['a', 'b'], match_method)
        assert mock_log_debug.call_args_list == [
            call('%s: %s', 'system', 'data'),
            call('%s: %s', 'system', 'error')
        ]

    @raises(KiwiCommandError)
    @patch('kiwi.command.Command')
    def test_poll_show_progress_raises(self, mock_command):
        match_method = CommandProcess(None).create_match_method(
            self.fake_matcher
        )
        process = CommandProcess(mock_command)
        process.command.process.poll = self.flow
        process.command.output_available = self.flow_out_available
        process.command.error_available = self.flow_err_available
        process.command.output.read = self.flow_out
        process.command.error.read = self.flow_err
        process.command.process.returncode = 1
        process.poll_show_progress(['a', 'b'], match_method)

    @patch('kiwi.command.Command')
    @patch('kiwi.logger.log.debug')
    def test_poll(self, mock_log_debug, mock_command):
        process = CommandProcess(mock_command)
        process.command.process.poll = self.flow
        process.command.output_available = self.flow_out_available
        process.command.error_available = self.flow_err_available
        process.command.output.read = self.flow_out
        process.command.error.read = self.flow_err
        process.command.process.returncode = 0
        process.poll()
        assert mock_log_debug.call_args_list == [
            call('%s: %s', 'system', 'data'),
            call('%s: %s', 'system', 'error')
        ]

    @raises(KiwiCommandError)
    @patch('kiwi.command.Command')
    def test_poll_raises(self, mock_command):
        process = CommandProcess(mock_command)
        process.command.process.poll = self.flow
        process.command.output_available = self.flow_out_available
        process.command.error_available = self.flow_err_available
        process.command.output.read = self.flow_out
        process.command.error.read = self.flow_err
        process.command.output.read.return_value = 'data'
        process.command.process.returncode = 1
        process.poll()

    @patch('kiwi.command.Command')
    @patch('kiwi.logger.log.debug')
    def test_poll_and_watch(self, mock_log_debug, mock_command):
        process = CommandProcess(mock_command)
        process.command.process.poll = self.flow
        process.command.output_available = self.flow_out_available
        process.command.error_available = self.flow_err_available
        process.command.output.read = self.flow_out
        process.command.error.read = self.flow_err
        process.command.process.returncode = 1
        result = process.poll_and_watch()
        call = mock_log_debug.call_args_list[0]
        assert mock_log_debug.call_args_list[0] == \
            call('--------------start--------------')
        call = mock_log_debug.call_args_list[1]
        assert mock_log_debug.call_args_list[1] == \
            call('data')
        call = mock_log_debug.call_args_list[2]
        assert mock_log_debug.call_args_list[2] == \
            call('--------------stop--------------')
        assert result.stderr == 'error'

    def test_create_match_method(self):
        match_method = CommandProcess(None).create_match_method(
            self.fake_matcher
        )
        assert match_method('a', 'b') == True

    @patch('kiwi.command.Command')
    def test_destructor(self, mock_command):
        process = CommandProcess(mock_command)
        process.command.process.returncode = None
        process.command.process.pid = 42
        process.command.process.kill = mock.Mock()
        process.__del__()
        process.command.process.kill.assert_called_once_with()
