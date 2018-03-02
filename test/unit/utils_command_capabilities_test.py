from mock import patch
from mock import call
from collections import namedtuple

from .test_helper import raises

from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.exceptions import KiwiCommandCapabilitiesError


class TestCommandCapabilities(object):
    @patch('kiwi.command.Command.run')
    def test_has_option_in_help(self, mock_run):
        command_type = namedtuple('command', ['output', 'error'])
        mock_run.return_value = command_type(
            output="Dummy line\n\t--some-flag\n\t--some-other-flag",
            error="Dummy line\n\t--error-flag\n\t--some-other-flag"
        )
        assert CommandCapabilities.has_option_in_help('command', '--some-flag')
        assert CommandCapabilities.has_option_in_help('command', '--error-flag')
        assert CommandCapabilities.has_option_in_help(
            'command', '--some-flag', help_flags=['subcommand', '-h']
        )
        assert CommandCapabilities.has_option_in_help(
            'command', '--some-other-flag',
            help_flags=['subcommand', '-h'], root='root_dir'
        )
        assert not CommandCapabilities.has_option_in_help(
            'command', '--non-existing-flag'
        )
        mock_run.assert_has_calls([
            call(['command', '--help']),
            call(['command', '--help']),
            call(['command', 'subcommand', '-h']),
            call(['chroot', 'root_dir', 'command', 'subcommand', '-h']),
            call(['command', '--help'])
        ])

    @patch('kiwi.command.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_has_option_in_help_command_failure_warning(
        self, mock_warn, mock_run
    ):
        def side_effect():
            raise Exception("Something went wrong")

        mock_run.side_effect = side_effect
        CommandCapabilities.has_option_in_help(
            'command_that_fails', '--non-existing-flag', raise_on_error=False
        )
        assert mock_warn.called

    @patch('kiwi.command.Command.run')
    @raises(KiwiCommandCapabilitiesError)
    def test_has_option_in_help_command_failure_exception(self, mock_run):
        def side_effect():
            raise Exception("Something went wrong")

        mock_run.side_effect = side_effect
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
    @raises(KiwiCommandCapabilitiesError)
    def test_check_version_no_match(self, mock_run):
        command_type = namedtuple('command', ['output'])
        mock_run.return_value = command_type(
            output="Dummy line\ncommand someother stuff\n"
        )
        CommandCapabilities.check_version('command', (1, 2, 3))

    @patch('kiwi.command.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_check_version_failure_warning(self, mock_warn, mock_run):
        def side_effect():
            raise Exception("Something went wrong")

        mock_run.side_effect = side_effect
        CommandCapabilities.check_version(
            'command_that_fails', (1, 2), raise_on_error=False
        )
        assert mock_warn.called

    @patch('kiwi.command.Command.run')
    @raises(KiwiCommandCapabilitiesError)
    def test_check_version_failure_exception(self, mock_run):
        def side_effect():
            raise Exception("Something went wrong")

        mock_run.side_effect = side_effect
        CommandCapabilities.check_version(
            'command_that_fails', '--non-existing-flag'
        )
