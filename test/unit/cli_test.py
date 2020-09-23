import sys
import logging
from mock import patch
from pytest import (
    raises, fixture
)

from .test_helper import argv_kiwi_tests

from kiwi.cli import Cli
from kiwi.exceptions import (
    KiwiCompatError,
    KiwiLoadCommandUndefined,
    KiwiCommandNotLoaded,
    KiwiUnknownServiceName
)


class TestCli:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.help_global_args = {
            'help': False,
            '--compat': False,
            'compat': False,
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
            '--shared-cache-dir': '/var/cache/kiwi',
            '--help': False
        }
        self.command_args = {
            '--add-repo': [],
            '--allow-existing-root': False,
            '--description': 'description',
            '--help': False,
            '--ignore-repos': False,
            '--ignore-repos-used-for-build': False,
            '--clear-cache': False,
            '--root': 'directory',
            '--set-repo': None,
            '--add-package': [],
            '--add-bootstrap-package': [],
            '--delete-package': [],
            '--set-container-derived-from': None,
            '--set-container-tag': None,
            '--add-container-label': [],
            '--signing-key': [],
            '-h': False,
            'help': False,
            'prepare': True,
            'system': True
        }
        self.cli = Cli()
        self.loaded_command = self.cli.load_command()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    @patch('kiwi.cli.Help.show')
    def test_show_and_exit_on_help_request(self, help_show):
        self.cli.all_args['help'] = True
        with raises(SystemExit):
            self.cli.show_and_exit_on_help_request()
        help_show.assert_called_once_with('kiwi')

    def test_get_servicename_system(self):
        cli = Cli()
        assert cli.get_servicename() == 'system'

    def test_get_servicename_compat_as_option(self):
        sys.argv = [
            sys.argv[0],
            '--compat', '--',
            '--build', 'description',
            '--type', 'oem',
            '-d', 'destination'
        ]
        cli = Cli()
        assert cli.get_servicename() == 'compat'

    def test_get_servicename_compat_as_service(self):
        sys.argv = [
            sys.argv[0],
            'compat',
            '--build', 'description',
            '--type', 'oem',
            '-d', 'destination'
        ]
        cli = Cli()
        assert cli.get_servicename() == 'compat'

    def test_warning_on_use_of_legacy_disk_type(self):
        sys.argv = [
            sys.argv[0],
            '--type', 'vmx', 'system', 'build',
            '--description', 'description',
            '--target-dir', 'directory'
        ]
        cli = Cli()
        with self._caplog.at_level(logging.WARNING):
            cli.get_global_args()
            assert 'vmx type is now a subset of oem, --type set to oem' in \
                self._caplog.text

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
            '--type', 'oem',
            '-d', 'destination'
        ]
        cli = Cli()
        cli.load_command()
        mock_compat.assert_called_once_with(
            ['--build', 'description', '--type', 'oem', '-d', 'destination']
        )

    @patch('kiwi.cli.Path.which')
    @patch('os.execvp')
    def test_invoke_kiwicompat_exec_failed(self, mock_exec, mock_which):
        mock_which.return_value = 'kiwicompat'
        mock_exec.side_effect = Exception
        with raises(KiwiCompatError):
            self.cli.invoke_kiwicompat([])

    def test_load_command_unknown(self):
        self.cli.loaded = False
        self.cli.all_args['<command>'] = 'foo'
        with raises(KiwiCommandNotLoaded):
            self.cli.load_command()

    def test_load_command_undefined(self):
        self.cli.loaded = False
        self.cli.all_args['<command>'] = None
        with raises(KiwiLoadCommandUndefined):
            self.cli.load_command()

    def test_get_command_args_not_loaded(self):
        sys.argv = [
            sys.argv[0], 'system', 'command-not-implemented'
        ]
        cli = Cli()
        with raises(KiwiCommandNotLoaded):
            cli.get_command_args()

    def test_get_servicename_unknown(self):
        self.cli.all_args['system'] = False
        self.cli.all_args['foo'] = False
        with raises(KiwiUnknownServiceName):
            self.cli.get_servicename()
