import sys

from mock import patch

from .test_helper import *

from kiwi.cli import Cli
from kiwi.exceptions import *


class TestCli(object):
    def setup(self):
        self.help_global_args = {
            'help': False,
            '--compat': False,
            '--type': None,
            'image': False,
            'system': True,
            '-h': False,
            '--logfile': None,
            '--color-output': False,
            '<legacy_args>': [],
            '--version': False,
            '--debug': False,
            'result': False,
            '--profile': [],
            '--help': False
        }
        self.command_args = {
            '--add-repo': [],
            '--allow-existing-root': False,
            '--description': 'description',
            '--help': False,
            '--ignore-repos': False,
            '--obs-repo-internal': False,
            '--root': 'directory',
            '--set-repo': None,
            '--add-package': [],
            '--delete-package': [],
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

    def test_get_servicename_system(self):
        sys.argv = [
            sys.argv[0],
            'system', 'prepare',
            '--description', 'description',
            '--root', 'directory'
        ]
        cli = Cli()
        assert cli.get_servicename() == 'system'

    def test_get_servicename_compat(self):
        sys.argv = [
            sys.argv[0],
            '--compat', '--',
            '--build', 'description',
            '--type', 'vmx',
            '-d', 'destination'
        ]
        cli = Cli()
        assert cli.get_servicename() == 'compat'

    def test_get_servicename_image(self):
        sys.argv = [
            sys.argv[0],
            'image', 'resize',
            '--target-dir', 'directory',
            '--size', '20g'
        ]
        cli = Cli()
        assert cli.get_servicename() == 'image'

    def test_get_servicename_result(self):
        sys.argv = [
            sys.argv[0],
            'result', 'list',
            '--target-dir', 'directory'
        ]
        cli = Cli()
        assert cli.get_servicename() == 'result'

    def test_get_command(self):
        assert self.cli.get_command() == 'prepare'

    def test_get_command_args(self):
        print(self.cli.get_command_args())
        assert self.cli.get_command_args() == self.command_args

    def test_get_global_args(self):
        assert self.cli.get_global_args() == self.help_global_args

    def test_load_command(self):
        assert self.cli.load_command() == self.loaded_command

    @patch('kiwi.cli.Cli.invoke_kiwicompat')
    def test_load_command_compat_mode(self, mock_compat):
        sys.argv = [
            sys.argv[0],
            '--compat', '--',
            '--build', 'description',
            '--type', 'vmx',
            '-d', 'destination'
        ]
        cli = Cli()
        cli.load_command()
        mock_compat.assert_called_once_with(
            ['--build', 'description', '--type', 'vmx', '-d', 'destination']
        )

    @raises(KiwiCompatError)
    @patch('os.path.exists')
    @patch('os.execvp')
    def test_invoke_kiwicompat_exec_failed(self, mock_exec, mock_exists):
        mock_exists.return_value = True
        mock_exec.side_effect = Exception
        self.cli.invoke_kiwicompat([])

    @raises(SystemExit)
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
