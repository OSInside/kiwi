from mock import patch
import mock

from kiwi.iso_tools import IsoTools


class TestIsoTools:
    def setup(self):
        self.runtime_config = mock.Mock()
        self.runtime_config.get_iso_tool_category = mock.Mock()

    @patch('kiwi.iso_tools.IsoToolsCdrTools')
    @patch('kiwi.iso_tools.RuntimeConfig')
    def test_iso_tools_cdrtools(
        self, mock_RuntimeConfig, mock_IsoToolsCdrTools
    ):
        self.runtime_config.get_iso_tool_category.return_value = 'cdrtools'
        mock_RuntimeConfig.return_value = self.runtime_config
        IsoTools('root-dir')
        mock_IsoToolsCdrTools.assert_called_once_with('root-dir')

    @patch('kiwi.iso_tools.IsoToolsXorrIso')
    @patch('kiwi.iso_tools.RuntimeConfig')
    def test_iso_tools_xorriso(
        self, mock_RuntimeConfig, mock_IsoToolsXorrIso
    ):
        self.runtime_config.get_iso_tool_category.return_value = 'xorriso'
        mock_RuntimeConfig.return_value = self.runtime_config
        IsoTools('root-dir')
        mock_IsoToolsXorrIso.assert_called_once_with('root-dir')
