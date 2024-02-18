from unittest.mock import patch

from kiwi.defaults import Defaults
from kiwi.iso_tools.iso import Iso


class TestIso:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.iso = Iso('source-dir')

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.iso_tools.iso.Command.run')
    def test_set_media_tag(self, mock_command):
        Iso.set_media_tag('foo')
        mock_command.assert_called_once_with(
            ['tagmedia', '--digest', 'sha256', '--check', '--pad', '0', 'foo']
        )
