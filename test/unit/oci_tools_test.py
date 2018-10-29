from pytest import raises
from mock import (
    patch, Mock
)

from kiwi.oci_tools import OCI

from kiwi.exceptions import (
    KiwiOCIArchiveToolError
)


class TestOCI(object):
    def setup(self):
        self.runtime_config = Mock()
        self.runtime_config.get_oci_archive_tool = Mock()

    @patch('kiwi.oci_tools.OCIUmoci')
    @patch('kiwi.oci_tools.RuntimeConfig')
    def test_oci_tool_umoci(
        self, mock_RuntimeConfig, mock_OCIUmoci
    ):
        self.runtime_config.get_oci_archive_tool.return_value = 'umoci'
        mock_RuntimeConfig.return_value = self.runtime_config
        OCI('tag_name')
        mock_OCIUmoci.assert_called_once_with('tag_name', None)

    @patch('kiwi.oci_tools.RuntimeConfig')
    def test_oci_tool_not_supported(self, mock_RuntimeConfig):
        self.runtime_config.get_oci_archive_tool.return_value = 'foo'
        mock_RuntimeConfig.return_value = self.runtime_config
        with raises(KiwiOCIArchiveToolError):
            OCI('tag_name')
