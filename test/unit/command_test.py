from mock import patch
from collections import namedtuple

import mock

import os

from .test_helper import raises

from kiwi.exceptions import (
    KiwiCommandError,
    KiwiCommandNotFound
)
from kiwi.command import Command


class TestCommand(object):
    @raises(KiwiCommandError)
    @patch('kiwi.path.Path.which')
    @patch('subprocess.Popen')
    def test_run_raises_error(self, mock_popen, mock_which):
        mock_which.return_value = 'command'
        mock_process = mock.Mock()
        mock_process.communicate = mock.Mock(
            return_value=[str.encode('stdout'), str.encode('stderr')]
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        Command.run(['command', 'args'])

    @raises(KiwiCommandError)
    @patch('kiwi.path.Path.which')
    @patch('subprocess.Popen')
    def test_run_failure(self, mock_popen, mock_which):
        mock_which.return_value = 'command'
        mock_popen.side_effect = KiwiCommandError('Run failure')
        Command.run(['command', 'args'])

    @raises(KiwiCommandError)
    def test_run_invalid_environment(self):
        Command.run(['command', 'args'], {'HOME': '/root'})

    @patch('kiwi.path.Path.which')
    @patch('subprocess.Popen')
    def test_run_does_not_raise_error(self, mock_popen, mock_which):
        mock_which.return_value = 'command'
        mock_process = mock.Mock()
        mock_process.communicate = mock.Mock(
            return_value=[str.encode('stdout'), str.encode('')]
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        result = Command.run(['command', 'args'], os.environ, False)
        assert result.error == '(no output on stderr)'
        assert result.output == 'stdout'

    @patch('kiwi.path.Path.which')
    def test_run_does_not_raise_error_if_command_not_found(self, mock_which):
        mock_which.return_value = None
        result = Command.run(['command', 'args'], os.environ, False)
        assert result.error is None
        assert result.output is None
        assert result.returncode == -1

    @patch('os.access')
    @patch('os.path.exists')
    @patch('subprocess.Popen')
    def test_run(self, mock_popen, mock_exists, mock_access):
        mock_exists.return_value = True
        command_run = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        run_result = command_run(
            output='stdout',
            error='stderr',
            returncode=0
        )
        mock_process = mock.Mock()
        mock_process.communicate = mock.Mock(
            return_value=[str.encode('stdout'), str.encode('stderr')]
        )
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        mock_access.return_value = True
        assert Command.run(['command', 'args']) == run_result

    @raises(KiwiCommandNotFound)
    def test_run_command_does_not_exist(self):
        Command.run(['does-not-exist'])

    @raises(KiwiCommandNotFound)
    def test_call_command_does_not_exist(self):
        Command.call(['does-not-exist'], os.environ)

    @patch('kiwi.path.Path.which')
    @patch('subprocess.Popen')
    @patch('select.select')
    def test_call(self, mock_select, mock_popen, mock_which):
        mock_which.return_value = 'command'
        mock_select.return_value = [True, False, False]
        mock_process = mock.Mock()
        mock_popen.return_value = mock_process
        call = Command.call(['command', 'args'])
        assert call.output_available()
        assert call.error_available()
        assert call.output == mock_process.stdout
        assert call.error == mock_process.stderr
        assert call.process == mock_process

    @raises(KiwiCommandError)
    @patch('kiwi.path.Path.which')
    @patch('subprocess.Popen')
    def test_call_failure(self, mock_popen, mock_which):
        mock_which.return_value = 'command'
        mock_popen.side_effect = KiwiCommandError('Call failure')
        Command.call(['command', 'args'])
