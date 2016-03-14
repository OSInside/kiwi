import sys

from mock import patch

from .test_helper import *

from kiwi.help import Help
from kiwi.exceptions import *


class TestHelp(object):
    def setup(self):
        self.help = Help()

    @raises(KiwiHelpNoCommandGiven)
    def test_show(self):
        self.help.show(None)

    @patch('subprocess.call')
    def test_show_command(self, mock_process):
        self.help.show('foo')
        mock_process.assert_called_once_with('man 2 foo', shell=True)
