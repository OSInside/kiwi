import sys
from unittest.mock import (
    patch, call
)
from pytest import (
    raises, fixture
)
import logging

from ..test_helper import argv_kiwi_tests

import kiwi.xml_parse
from kiwi.tasks.base import CliTask

from kiwi.defaults import Defaults
from kiwi.exceptions import KiwiConfigFileNotFound


class TestCliTask:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.logger.Logger.setLogLevel')
    @patch('kiwi.logger.Logger.setLogFlag')
    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.logger.Logger.set_log_socket')
    @patch('kiwi.logger.Logger.set_color_format')
    @patch('kiwi.cli.Cli.show_and_exit_on_help_request')
    @patch('kiwi.cli.Cli.load_command')
    @patch('kiwi.cli.Cli.get_command_args')
    @patch('kiwi.cli.Cli.get_global_args')
    @patch('kiwi.runtime_config.RuntimeConfig')
    def setup(
        self, mock_runtime_config, mock_global_args, mock_command_args,
        mock_load_command, mock_help_check, mock_color,
        mock_set_log_socket, mock_setlog, mock_setLogFlag, mock_setLogLevel
    ):
        Defaults.set_platform_name('x86_64')
        mock_global_args.return_value = {
            '--debug': True,
            '--debug-run-scripts-in-screen': True,
            '--logfile': 'stdout',
            '--logsocket': 'log_socket',
            '--loglevel': None,
            '--color-output': True,
            '--profile': ['vmxFlavour'],
            '--type': None
        }
        mock_command_args.return_value = {
            'system': True,
            'prepare': True,
            '--description': 'description',
            '--root': 'directory'
        }

        self.task = CliTask()

        mock_help_check.assert_called_once_with()
        mock_load_command.assert_called_once_with()
        mock_command_args.assert_called_once_with()
        mock_global_args.assert_called_once_with()
        assert mock_setLogLevel.call_args_list == [
            call(logging.DEBUG),
            call(logging.CRITICAL, except_for=['file', 'socket'])
        ]
        mock_setLogFlag.assert_called_once_with('run-scripts-in-screen')
        mock_setlog.assert_called_once_with('stdout')
        mock_color.assert_called_once_with()
        mock_runtime_config.assert_called_once_with()

        mock_setLogLevel.reset_mock()
        mock_global_args.return_value = {
            '--debug': True,
            '--debug-run-scripts-in-screen': True,
            '--logfile': 'some',
            '--logsocket': 'log_socket',
            '--loglevel': None,
            '--color-output': True,
            '--profile': ['vmxFlavour'],
            '--type': None
        }
        self.task = CliTask()
        assert mock_setLogLevel.call_args_list == [
            call(logging.DEBUG),
            call(logging.DEBUG, only_for=['file', 'socket'])
        ]

    @patch('kiwi.logger.Logger.setLogLevel')
    @patch('kiwi.logger.Logger.setLogFlag')
    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.logger.Logger.set_log_socket')
    @patch('kiwi.logger.Logger.set_color_format')
    @patch('kiwi.cli.Cli.show_and_exit_on_help_request')
    @patch('kiwi.cli.Cli.load_command')
    @patch('kiwi.cli.Cli.get_command_args')
    @patch('kiwi.cli.Cli.get_global_args')
    @patch('kiwi.runtime_config.RuntimeConfig')
    def setup_method(
        self, cls, mock_runtime_config, mock_global_args, mock_command_args,
        mock_load_command, mock_help_check, mock_color,
        mock_set_log_socket, mock_setlog, mock_setLogFlag, mock_setLogLevel
    ):
        self.setup()

    @patch('kiwi.logger.Logger.setLogLevel')
    @patch('kiwi.cli.Cli.load_command')
    @patch('kiwi.cli.Cli.get_command_args')
    @patch('kiwi.cli.Cli.get_global_args')
    @patch('kiwi.runtime_config.RuntimeConfig')
    def test_setup_custom_log_level(
        self, mock_runtime_config, mock_global_args, mock_command_args,
        mock_load_command, mock_setLogLevel
    ):
        Defaults.set_platform_name('x86_64')
        mock_global_args.return_value = {
            '--debug': None,
            '--logfile': None,
            '--logsocket': None,
            '--debug-run-scripts-in-screen': None,
            '--color-output': None,
            '--loglevel': '10',
        }
        self.task = CliTask()
        mock_setLogLevel.assert_called_once_with(10)

    @patch('kiwi.logger.Logger.setLogLevel')
    @patch('kiwi.cli.Cli.load_command')
    @patch('kiwi.cli.Cli.get_command_args')
    @patch('kiwi.cli.Cli.get_global_args')
    @patch('kiwi.runtime_config.RuntimeConfig')
    def test_setup_custom_log_level_invalid(
        self, mock_runtime_config, mock_global_args, mock_command_args,
        mock_load_command, mock_setLogLevel
    ):
        Defaults.set_platform_name('x86_64')
        mock_global_args.return_value = {
            '--debug': None,
            '--logfile': None,
            '--logsocket': None,
            '--debug-run-scripts-in-screen': None,
            '--color-output': None,
            '--loglevel': 'bogus',
        }
        self.task = CliTask()
        mock_setLogLevel.assert_called_once_with(20)

    def test_quadruple_token(self):
        assert self.task.quadruple_token('a,b') == ['a', 'b', None, None]

    def test_tentuple_token(self):
        assert self.task.tentuple_token(
            'a,b,,d,e,f,{1;2;3},x y z,jammy,false'
        ) == [
            'a', 'b', '', 'd', 'e', 'f', ['1', '2', '3'], 'x y z',
            'jammy', False
        ]
        assert self.task.tentuple_token('a,b,,d,e,f,{1;2;3}') == [
            'a', 'b', '', 'd', 'e', 'f', ['1', '2', '3'],
            None, None, None
        ]

    def test_attr_token(self):
        assert self.task.attr_token('a=b') == ['a', 'b']

    @patch('kiwi.tasks.base.RuntimeChecker')
    def test_load_xml_description(self, mock_runtime_checker):
        self.task.load_xml_description('../data/description')
        mock_runtime_checker.assert_called_once_with(self.task.xml_state)
        assert self.task.config_file == '../data/description/config.xml'
        assert isinstance(self.task.xml_data, kiwi.xml_parse.image)
        assert self.task.xml_state.profiles == ['vmxFlavour']

    def test_load_xml_description_buildservice(self):
        self.task.load_xml_description('../data/description.buildservice')
        assert self.task.config_file == \
            '../data/description.buildservice/appliance.kiwi'

    def test_load_xml_description_raises(self):
        with raises(KiwiConfigFileNotFound):
            self.task.load_xml_description('foo')
        with raises(KiwiConfigFileNotFound):
            self.task.load_xml_description('path', 'custom_kiwi_file')

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()
