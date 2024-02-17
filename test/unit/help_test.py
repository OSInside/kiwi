from unittest.mock import patch
from pytest import raises

from kiwi.help import Help

from kiwi.exceptions import KiwiHelpNoCommandGiven


class TestHelp:
    def setup(self):
        self.help = Help()

    def setup_method(self, cls):
        self.setup()

    def test_show(self):
        with raises(KiwiHelpNoCommandGiven):
            self.help.show(None)

    @patch('subprocess.call')
    def test_show_command(self, mock_process):
        self.help.show('foo')
        mock_process.assert_called_once_with('man 8 foo', shell=True)
