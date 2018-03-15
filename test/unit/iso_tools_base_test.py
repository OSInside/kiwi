from mock import patch
from .test_helper import raises

from kiwi.iso_tools.base import IsoToolsBase


class TestIsoToolsBase(object):
    @patch('platform.machine')
    def setup(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        self.iso_tool = IsoToolsBase('source-dir')

    def test_get_iso_creation_parameters(self):
        assert self.iso_tool.get_iso_creation_parameters() == []

    @raises(NotImplementedError)
    def test_get_tool_name(self):
        self.iso_tool.get_tool_name()

    @raises(NotImplementedError)
    def test_init_iso_creation_parameters(self):
        self.iso_tool.init_iso_creation_parameters('sortfile')

    @raises(NotImplementedError)
    def test_add_efi_loader_parameters(self):
        self.iso_tool.add_efi_loader_parameters()
