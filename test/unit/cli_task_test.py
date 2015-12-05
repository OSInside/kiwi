import sys
import mock
from nose.tools import *
from mock import patch

import logging
import nose_helper
import inspect

from kiwi.cli_task import CliTask
from kiwi.exceptions import *

import kiwi.xml_parse


class TestCliTask(object):
    @patch('os.path.isfile')
    @patch('ConfigParser.ConfigParser.has_section')
    @patch('kiwi.logger.log.setLogLevel')
    @patch('kiwi.logger.log.set_logfile')
    @patch('kiwi.cli.Cli.show_and_exit_on_help_request')
    def setup(
        self, mock_help, mock_setlog, mock_setlevel, mock_section, mock_isfile
    ):
        sys.argv = [
            sys.argv[0],
            '--debug',
            '--logfile', 'log',
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

    def test_quadruple_token(self):
        assert self.task.quadruple_token('a,b') == ['a', 'b', None, None]

    def test_load_xml_description(self):
        self.task.load_xml_description('../data/description')
        assert self.task.config_file == '../data/description/config.xml'
        assert isinstance(self.task.xml_data, kiwi.xml_parse.image)
        assert self.task.xml_state.profiles == ['vmxFlavour']

    @raises(KiwiConfigFileNotFound)
    def test_load_xml_description_raises(self):
        self.task.load_xml_description('foo')
