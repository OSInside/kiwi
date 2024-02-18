import logging
from unittest.mock import (
    patch, call
)
from pytest import (
    raises, fixture
)
from collections import namedtuple

from kiwi.utils.command_capabilities import CommandCapabilities

from kiwi.exceptions import KiwiCommandCapabilitiesError


class TestCommandCapabilities:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('kiwi.command.Command.run')
    def test_has_option_in_help(self, mock_run):
        command_type = namedtuple('command', ['output', 'error'])
        mock_run.return_value = command_type(
            output="Dummy line\n\t--some-flag\n\t--some-other-flag",
            error="Dummy line\n\t--error-flag\n\t--some-other-flag"
        )
        assert CommandCapabilities.has_option_in_help(
            'command', '--some-flag'
        ) is True
        assert CommandCapabilities.has_option_in_help(
            'command', '--error-flag'
        ) is True
        assert CommandCapabilities.has_option_in_help(
            'command', '--some-flag', help_flags=['subcommand', '-h']
        ) is True
        assert CommandCapabilities.has_option_in_help(
            'command', '--some-other-flag',
            help_flags=['subcommand', '-h'], root='root_dir'
        ) is True
        assert CommandCapabilities.has_option_in_help(
            'command', '--non-existing-flag', raise_on_error=False
        ) is False
        mock_run.assert_has_calls(
            [
                call(['command', '--help'], raise_on_error=False),
                call(['command', '--help'], raise_on_error=False),
                call(['command', 'subcommand', '-h'], raise_on_error=False),
                call(
                    ['chroot', 'root_dir', 'command', 'subcommand', '-h'],
                    raise_on_error=False
                ),
                call(['command', '--help'], raise_on_error=False)
            ]
        )

    @patch('kiwi.command.Command.run')
    def test_has_option_in_help_command_failure_warning(self, mock_run):
        mock_run.return_value.output = ''
        mock_run.return_value.error = ''
        with self._caplog.at_level(logging.WARNING):
            CommandCapabilities.has_option_in_help(
                'command_that_fails', '--non-existing-flag',
                raise_on_error=False
            )

    @patch('kiwi.command.Command.run')
    def test_has_option_in_help_command_failure_exception(self, mock_run):
        mock_run.return_value.output = ''
        mock_run.return_value.error = ''
        with raises(KiwiCommandCapabilitiesError):
            CommandCapabilities.has_option_in_help(
                'command_that_fails', '--non-existing-flag'
            )

    @patch('kiwi.command.Command.run')
    def test_check_version(self, mock_run):
        command_type = namedtuple('command', ['output'])
        mock_run.return_value = command_type(
            output="Dummy line\ncommand v1.2.3\n"
        )
        assert CommandCapabilities.check_version('command', (1, 2, 3))
        assert CommandCapabilities.check_version('command', (1, 1, 3))
        assert not CommandCapabilities.check_version('command', (1, 3))
        assert CommandCapabilities.check_version(
            'command', (1, 2, 3), version_flags=['-v']
        )
        assert CommandCapabilities.check_version(
            'command', (1, 2, 3), version_flags=['-v'], root='root_dir'
        )
        mock_run.assert_has_calls([
            call(['command', '--version']),
            call(['command', '--version']),
            call(['command', '--version']),
            call(['command', '-v']),
            call(['chroot', 'root_dir', 'command', '-v'])
        ])

    @patch('kiwi.command.Command.run')
    def test_check_version_complex_pattern(self, mock_run):
        command_type = namedtuple('command', ['output'])
        mock_run.return_value = command_type(
            output="grub2-mkconfig (GRUB2) 2.02\n"
        )
        assert CommandCapabilities.check_version('command', (2, 2)) is True
        assert CommandCapabilities.check_version('command', (2, 4)) is False

    @patch('kiwi.command.Command.run')
    def test_check_version_no_match(self, mock_run):
        command_type = namedtuple('command', ['output'])
        mock_run.return_value = command_type(
            output="Dummy line\ncommand someother stuff\n"
        )
        with raises(KiwiCommandCapabilitiesError):
            CommandCapabilities.check_version('command', (1, 2, 3))

    @patch('kiwi.command.Command.run')
    def test_check_version_failure_warning(self, mock_run):
        def side_effect():
            raise Exception("Something went wrong")

        mock_run.side_effect = side_effect
        with self._caplog.at_level(logging.WARNING):
            CommandCapabilities.check_version(
                'command_that_fails', (1, 2), raise_on_error=False
            )

    @patch('kiwi.command.Command.run')
    def test_check_version_failure_exception(self, mock_run):
        def side_effect():
            raise Exception("Something went wrong")

        mock_run.side_effect = side_effect
        with raises(KiwiCommandCapabilitiesError):
            CommandCapabilities.check_version(
                'command_that_fails', '--non-existing-flag'
            )
