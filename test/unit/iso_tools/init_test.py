from pytest import raises
from unittest.mock import patch
import unittest.mock as mock

from kiwi.iso_tools import IsoTools
from kiwi.exceptions import KiwiIsoToolError


class TestIsoTools:
    def setup(self):
        self.runtime_config = mock.Mock()
        self.runtime_config.get_iso_tool_category = mock.Mock()

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.iso_tools.xorriso.IsoToolsXorrIso')
    @patch('kiwi.iso_tools.RuntimeConfig')
    def test_iso_tools_xorriso(
        self, mock_RuntimeConfig, mock_IsoToolsXorrIso
    ):
        self.runtime_config.get_iso_tool_category.return_value = 'xorriso'
        mock_RuntimeConfig.return_value = self.runtime_config
        IsoTools.new('root-dir')
        mock_IsoToolsXorrIso.assert_called_once_with('root-dir')

    @patch('kiwi.iso_tools.RuntimeConfig')
    def test_iso_tools_unsupported(self, mock_RuntimeConfig):
        self.runtime_config.get_iso_tool_category.return_value = 'foo'
        mock_RuntimeConfig.return_value = self.runtime_config
        with raises(KiwiIsoToolError):
            IsoTools.new('root_dir')
