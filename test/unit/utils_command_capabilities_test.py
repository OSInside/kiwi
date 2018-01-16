from mock import patch
from mock import call
from collections import namedtuple

from kiwi.utils.command_capabilities import CommandCapabilities


class TestCommandCapabilities(object):
    @patch('kiwi.command.Command.run')
    def test_has_option_in_help(self, mock_run):
        command_type = namedtuple('command', ['output'])
        mock_run.return_value = command_type(
            output="Dummy line\n\t--some-flag\n\t--some-other-flag"
        )
        assert CommandCapabilities.has_option_in_help('command', '--some-flag')
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
            call(['command', 'subcommand', '-h']),
            call(['chroot', 'root_dir', 'command', 'subcommand', '-h']),
            call(['command', '--help'])
        ])

    @patch('kiwi.command.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_has_option_in_help_command_failure(self, mock_warn, mock_run):
        def side_effect():
            raise Exception("Something went wrong")

        mock_run.side_effect = side_effect
        CommandCapabilities.has_option_in_help(
            'command_that_fails', '--non-existing-flag'
        )
        assert mock_warn.called
