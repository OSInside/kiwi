import sys
import mock

from mock import patch

import logging
from .test_helper import *
import inspect

from kiwi.tasks.base import CliTask
from kiwi.exceptions import *

import kiwi.xml_parse


class TestCliTask(object):
    @patch('os.path.isfile')
    @patch('configparser.ConfigParser.has_section')
    @patch('kiwi.logger.log.setLogLevel')
    @patch('kiwi.logger.log.set_logfile')
    @patch('kiwi.logger.log.set_color_format')
    @patch('kiwi.cli.Cli.show_and_exit_on_help_request')
    def setup(
        self, mock_help, mock_color, mock_setlog, mock_setlevel,
        mock_section, mock_isfile
    ):
        sys.argv = [
            sys.argv[0],
            '--debug',
            '--logfile', 'log',
            '--color-output',
            '--profile', 'vmxFlavour',
            'system',
            'prepare',
            '--description', 'description',
            '--root', 'directory'
        ]
        self.task = CliTask()

        mock_help.assert_called_once_with()
        mock_setlevel.assert_called_once_with(logging.DEBUG)
        mock_setlog.assert_called_once_with('log')
        mock_color.assert_called_once_with()

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

    @raises(KiwiConfigFileNotFound)
    def test_load_xml_description_raises(self):
        self.task.load_xml_description('foo')
