import sys
from mock import patch
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
    @patch('kiwi.logger.Logger.set_logfile')
    @patch('kiwi.logger.Logger.set_color_format')
    @patch('kiwi.cli.Cli.show_and_exit_on_help_request')
    @patch('kiwi.cli.Cli.load_command')
    @patch('kiwi.cli.Cli.get_command_args')
    @patch('kiwi.cli.Cli.get_global_args')
    @patch('kiwi.tasks.base.RuntimeConfig')
    def setup(
        self, mock_runtime_config, mock_global_args, mock_command_args,
        mock_load_command, mock_help_check, mock_color,
        mock_setlog, mock_setlevel
    ):
        Defaults.set_platform_name('x86_64')
        mock_global_args.return_value = {
            '--debug': True,
            '--logfile': 'log',
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
        mock_setlevel.assert_called_once_with(logging.DEBUG)
        mock_setlog.assert_called_once_with('log')
        mock_color.assert_called_once_with()
        mock_runtime_config.assert_called_once_with()

    def test_quadruple_token(self):
        assert self.task.quadruple_token('a,b') == ['a', 'b', None, None]

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

    def teardown(self):
        sys.argv = argv_kiwi_tests
