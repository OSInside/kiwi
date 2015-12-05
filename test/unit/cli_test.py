import sys
from nose.tools import *
from mock import patch

import nose_helper

from kiwi.cli import Cli
from kiwi.exceptions import *


class TestCli(object):
    def setup(self):
        self.help_global_args = {
            'help': False,
            '--type': None,
            'system': True,
            '-h': False,
            '--logfile': None,
            '--version': False,
            '--debug': False,
            '--profile': [],
            '--help': False
        }
        self.command_args = {
            '--add-repo': [],
            '--allow-existing-root': False,
            '--description': 'description',
            '--help': False,
            '--root': 'directory',
            '--set-repo': None,
            '-h': False,
            'help': False,
            'prepare': True,
            'system': True
        }
        sys.argv = [
            sys.argv[0],
            'system', 'prepare',
            '--description', 'description',
            '--root', 'directory'
        ]
        self.cli = Cli()
        self.loaded_command = self.cli.load_command()

    @raises(SystemExit)
    @patch('kiwi.cli.Help.show')
    def test_show_and_exit_on_help_request(self, help_show):
        self.cli.all_args['help'] = True
        self.cli.show_and_exit_on_help_request()
        help_show.assert_called_once_with('kiwi')

    def test_get_servicename(self):
        assert self.cli.get_servicename() == 'system'

    def test_get_command(self):
        assert self.cli.get_command() == 'prepare'

    def test_get_command_args(self):
        print self.cli.get_command_args()
        assert self.cli.get_command_args() == self.command_args

    def test_get_global_args(self):
        print self.cli.get_global_args()
        assert self.cli.get_global_args() == self.help_global_args

    def test_load_command(self):
        assert self.cli.load_command() == self.loaded_command

    @raises(KiwiUnknownCommand)
    def test_load_command_unknown(self):
        self.cli.loaded = False
        self.cli.all_args['<command>'] = 'foo'
        self.cli.load_command()

    @raises(KiwiLoadCommandUndefined)
    def test_load_command_undefined(self):
        self.cli.loaded = False
        self.cli.all_args['<command>'] = None
        self.cli.load_command()

    @raises(KiwiCommandNotLoaded)
    def test_get_command_args_not_loaded(self):
        sys.argv = [
            sys.argv[0], 'system', 'command-not-implemented'
        ]
        cli = Cli()
        cli.get_command_args()

    @raises(KiwiUnknownServiceName)
    def test_get_servicename_unknown(self):
        self.cli.all_args['system'] = False
        self.cli.all_args['foo'] = False
        self.cli.get_servicename()
