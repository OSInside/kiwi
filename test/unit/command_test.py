from nose.tools import *
from mock import patch
from collections import namedtuple

import mock

import nose_helper

from kiwi.exceptions import KiwiCommandError
from kiwi.command import Command


class TestCommand(object):
    @raises(KiwiCommandError)
    @patch('subprocess.Popen')
    def test_run_raises_error(self, mock_popen):
        mock_process = mock.Mock()
        mock_process.communicate = mock.Mock(
            return_value=['stdout', 'stderr']
        )
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        Command.run(['command', 'args'])

    @patch('subprocess.Popen')
    def test_run(self, mock_popen):
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
            return_value=['stdout', 'stderr']
        )
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        assert Command.run(['command', 'args']) == run_result

    @raises(KiwiCommandError)
    def test_run_command_does_not_exist(self):
        Command.run(['does-not-exist'])

    @raises(KiwiCommandError)
    def test_call_command_does_not_exist(self):
        Command.call(['does-not-exist'])

    @patch('subprocess.Popen')
    @patch('select.select')
    def test_call(self, mock_select, mock_popen):
        mock_select.return_value = [True, False, False]
        mock_process = mock.Mock()
        mock_popen.return_value = mock_process
        command_call = namedtuple(
            'command', [
                'output', 'output_available',
                'error', 'error_available',
                'process'
            ]
        )
        call = Command.call(['command', 'args'])
        assert call.output_available()
        assert call.error_available()
        assert call.output == mock_process.stdout
        assert call.error == mock_process.stderr
        assert call.process == mock_process
