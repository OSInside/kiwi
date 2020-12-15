from pytest import raises
from mock import (
    patch, Mock
)

from kiwi.oci_tools import OCI

from kiwi.exceptions import (
    KiwiOCIArchiveToolError
)


class TestOCI:
    def setup(self):
        self.runtime_config = Mock()
        self.runtime_config.get_oci_archive_tool = Mock()

    @patch('kiwi.oci_tools.umoci.OCIUmoci')
    @patch('kiwi.oci_tools.RuntimeConfig')
    def test_oci_tool_umoci(
        self, mock_RuntimeConfig, mock_OCIUmoci
    ):
        self.runtime_config.get_oci_archive_tool.return_value = 'umoci'
        mock_RuntimeConfig.return_value = self.runtime_config
        OCI.new()
        mock_OCIUmoci.assert_called_once_with()

    @patch('kiwi.oci_tools.buildah.OCIBuildah')
    @patch('kiwi.oci_tools.RuntimeConfig')
    def test_oci_tool_buildah(
        self, mock_RuntimeConfig, mock_OCIBuildah
    ):
        self.runtime_config.get_oci_archive_tool.return_value = 'buildah'
        mock_RuntimeConfig.return_value = self.runtime_config
        OCI.new()
        mock_OCIBuildah.assert_called_once_with()

    @patch('kiwi.oci_tools.RuntimeConfig')
    def test_oci_tool_not_supported(self, mock_RuntimeConfig):
        self.runtime_config.get_oci_archive_tool.return_value = 'foo'
        mock_RuntimeConfig.return_value = self.runtime_config
        with raises(KiwiOCIArchiveToolError):
            OCI.new()
