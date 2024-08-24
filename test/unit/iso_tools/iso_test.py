from unittest.mock import patch, Mock

from kiwi.defaults import Defaults
from kiwi.iso_tools.iso import Iso


class TestIso:
    def setup(self):
        Defaults.set_platform_name('x86_64')
        self.iso = Iso('source-dir')

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.iso_tools.iso.Command.run')
    @patch('kiwi.iso_tools.iso.RuntimeConfig')
    def test_set_media_tag_checkmedia(self, mock_RuntimeConfig, mock_command):
        runtime_config = Mock()
        runtime_config.get_iso_media_tag_tool.return_value = 'checkmedia'
        mock_RuntimeConfig.return_value = runtime_config
        Iso.set_media_tag('foo')
        mock_command.assert_called_once_with(
            ['tagmedia', '--digest', 'sha256', '--check', '--pad', '0', 'foo']
        )

    @patch('kiwi.iso_tools.iso.Command.run')
    @patch('kiwi.iso_tools.iso.RuntimeConfig')
    def test_set_media_tag_isomd5sum(self, mock_RuntimeConfig, mock_command):
        runtime_config = Mock()
        runtime_config.get_iso_media_tag_tool.return_value = 'isomd5sum'
        mock_RuntimeConfig.return_value = runtime_config
        Iso.set_media_tag('foo')
        mock_command.assert_called_once_with(
            ['implantisomd5', '--force', 'foo']
        )
