import sys
import logging
from unittest.mock import patch
from pytest import (
    raises, fixture
)

from .test_helper import argv_kiwi_tests

from kiwi.cli import Cli
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiLoadCommandUndefined,
    KiwiCommandNotLoaded,
    KiwiUnknownServiceName
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
            '-h': False,
            '--logfile': None,
            '--logsocket': None,
            '--loglevel': None,
            '--color-output': False,
            '--version': False,
            '--debug': False,
            '--debug-run-scripts-in-screen': False,
            'result': False,
            '--profile': [],
            '--shared-cache-dir': '/var/cache/kiwi',
            '--temp-dir': '/var/tmp',
            '--target-arch': None,
            '--help': False,
            '--config': 'config-file',
            '--kiwi-file': None
        }
        self.command_args = {
            '--add-repo': [],
            '--add-repo-credentials': [],
            '--set-type-attr': [],
            '--set-release-version': None,
            '--allow-existing-root': False,
            '--description': 'description',
            '--help': False,
            '--ignore-repos': False,
            '--ignore-repos-used-for-build': False,
            '--clear-cache': False,
            '--root': 'directory',
            '--set-repo': None,
            '--set-repo-credentials': None,
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

    def setup_method(self, cls):
        self.setup()

    def teardown(self):
        sys.argv = argv_kiwi_tests

    def teardown_method(self, cls):
        self.teardown()

    @patch('kiwi.cli.Help.show')
    def test_show_and_exit_on_help_request(self, help_show):
        self.cli.all_args['help'] = True
        with raises(SystemExit):
            self.cli.show_and_exit_on_help_request()
        help_show.assert_called_once_with('kiwi')

    def test_get_servicename_system(self):
        cli = Cli()
        assert cli.get_servicename() == 'system'

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

    def test_set_target_arch(self):
        sys.argv = [
            sys.argv[0],
            '--target-arch', 'x86_64', 'system', 'build',
            '--description', 'description',
            '--target-dir', 'directory'
        ]
        cli = Cli()
        cli.get_global_args()
        assert Defaults.get_platform_name() == 'x86_64'

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

    def test_load_command(self):
        assert self.cli.load_command() == self.loaded_command

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
