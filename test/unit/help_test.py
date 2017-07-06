from mock import patch

from .test_helper import raises

from kiwi.help import Help

from kiwi.exceptions import KiwiHelpNoCommandGiven


class TestHelp(object):
    def setup(self):
        self.help = Help()

    @raises(KiwiHelpNoCommandGiven)
    def test_show(self):
        self.help.show(None)

    @patch('subprocess.call')
    def test_show_command(self, mock_process):
        self.help.show('foo')
        mock_process.assert_called_once_with('man 8 foo', shell=True)
