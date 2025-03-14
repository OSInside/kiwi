import sys
import logging
import typer
from unittest.mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)

from .test_helper import argv_kiwi_tests

from kiwi.cli import Cli
from kiwi.defaults import Defaults
from kiwi.version import __version__

from kiwi.exceptions import (
    KiwiLoadCommandUndefined,
    KiwiCommandNotLoaded,
    KiwiUnknownServiceName,
    KiwiLoadPluginError
)


class TestCli:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.expected_global_args = {
            'help': False,
            '--type': None,
            'image': False,
            'system': True,
            '--logfile': None,
            '--logsocket': None,
            '--loglevel': None,
            '--color-output': False,
            '--debug': False,
            '--debug-run-scripts-in-screen': False,
            'result': False,
            '--profile': [],
            '--setenv': [],
            '--shared-cache-dir': '/var/cache/kiwi',
            '--temp-dir': '/var/tmp',
            '--target-arch': None,
            '--config': None,
            '--kiwi-file': None
        }
        self.command_args = {
            '--add-repo': [],
            '--add-repo-credentials': [],
            '--set-type-attr': [],
            '--set-release-version': None,
            '--allow-existing-root': False,
            '--description': 'description',
            '--ignore-repos': False,
            '--ignore-repos-used-for-build': False,
            '--clear-cache': False,
            '--root': 'directory',
            '--set-repo': None,
            '--set-repo-credentials': None,
            '--add-package': [],
            '--add-bootstrap-package': [],
            '--ca-cert': [],
            '--ca-target-distribution': None,
            '--delete-package': [],
            '--set-container-derived-from': None,
            '--set-container-tag': None,
            '--add-container-label': [],
            '--signing-key': [],
            'help': False,
            'prepare': True,
            'command': 'prepare',
            'system': True
        }
        self.command_args.update(
            self.expected_global_args
        )
        self.cli = Cli()
        self.loaded_command = self.cli.load_command()

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    def test_get_servicename_system(self):
        cli = Cli()
        assert cli.get_servicename() == 'system'

    def test_get_command_args(self):
        with patch(
            'sys.argv', [
                sys.argv[0],
                '--temp-dir', '/var/tmp',
                '--shared-cache-dir', '/var/cache/kiwi',
                'system', 'prepare',
                '--description', 'description',
                '--root', 'directory'
            ]
        ):
            cli = Cli()
            assert cli.get_command_args() == self.command_args
        with patch(
            'sys.argv', [
                sys.argv[0],
                'system', 'prepare',
                '--description', 'description',
                '--root', 'directory'
            ]
        ):
            cli = Cli()
            assert cli.get_command_args() == self.command_args

    def test_warning_on_use_of_legacy_disk_type(self):
        with patch(
            'sys.argv', [
                sys.argv[0],
                '--type', 'vmx', 'system', 'build',
                '--description', 'description',
                '--target-dir', 'directory'
            ]
        ):
            cli = Cli()
            with self._caplog.at_level(logging.WARNING):
                cli.get_global_args()
                assert 'vmx type is now a subset of oem, --type set to oem' in \
                    self._caplog.text

    def test_set_target_arch(self):
        with patch(
            'sys.argv', [
                sys.argv[0],
                '--target-arch', 'x86_64', 'system', 'build',
                '--description', 'description',
                '--target-dir', 'directory'
            ]
        ):
            cli = Cli()
            cli.get_global_args()
            assert Defaults.get_platform_name() == 'x86_64'

    def test_get_servicename_image(self):
        with patch(
            'sys.argv', [
                sys.argv[0],
                'image', 'resize',
                '--target-dir', 'directory',
                '--size', '20g'
            ]
        ):
            cli = Cli()
            assert cli.get_servicename() == 'image'

    def test_get_servicename_result(self):
        with patch(
            'sys.argv', [
                sys.argv[0],
                'result', 'list',
                '--target-dir', 'directory'
            ]
        ):
            cli = Cli()
            assert cli.get_servicename() == 'result'

    def test_get_command(self):
        assert self.cli.get_command() == 'prepare'

    def test_load_command(self):
        assert self.cli.load_command() == self.loaded_command

    def test_load_command_unknown(self):
        self.cli.loaded = False
        self.cli.global_args['command'] = 'foo'
        with raises(KiwiCommandNotLoaded):
            self.cli.load_command()

    def test_load_command_undefined(self):
        self.cli.loaded = False
        self.cli.global_args['command'] = None
        with raises(KiwiLoadCommandUndefined):
            self.cli.load_command()

    def test_get_command_args_not_loaded(self):
        with patch(
            'sys.argv', [
                sys.argv[0], 'system', 'command-not-implemented'
            ]
        ):
            with patch('sys.exit'):
                cli = Cli()
                with raises(KiwiCommandNotLoaded):
                    cli.get_command_args()

    @patch('builtins.print')
    def test_kiwi_version(self, mock_print):
        with patch(
            'sys.argv', [
                sys.argv[0], '--version'
            ]
        ):
            with patch('sys.exit'):
                Cli()
            mock_print.assert_called_once_with(
                f'KIWI (next generation) version {__version__}'
            )

    @patch('kiwi.cli.Help')
    def test_help(self, mock_Help):
        manual = Mock()
        mock_Help.return_value = manual
        with patch(
            'sys.argv', [
                sys.argv[0], 'help'
            ]
        ):
            with patch('sys.exit'):
                Cli()
            manual.show.assert_called_once_with('kiwi')

    @patch.object(Cli, '_get_module_entries')
    @patch('kiwi.cli.EntryPoint')
    def test_load_plugin_cli(
        self, mock_EntryPoint, mock_get_module_entries
    ):
        plugin_entry = Mock()
        mock_EntryPoint.return_value = plugin_entry
        entry = Mock(
            name='system_boxbuild',
            value='kiwi_boxed_plugin.tasks.system_boxbuild',
            group='kiwi.tasks'
        )
        mock_get_module_entries.return_value = [entry]
        with patch(
            'sys.argv', [
                sys.argv[0],
                'system', 'build',
                '--description', 'description',
                '--target-dir', 'directory'
            ]
        ):
            plugin_entry.load.return_value.typers = {
                'some': typer.Typer()
            }
            cli = Cli()
            plugin_entry.load.side_effect = ModuleNotFoundError
            cli.load_plugin_cli()
            plugin_entry.load.side_effect = Exception('error')
            with raises(KiwiLoadPluginError):
                cli.load_plugin_cli()

    def test_get_servicename_unknown(self):
        self.cli.global_args['image'] = False
        self.cli.global_args['system'] = False
        self.cli.global_args['result'] = False
        with raises(KiwiUnknownServiceName):
            self.cli.get_servicename()
