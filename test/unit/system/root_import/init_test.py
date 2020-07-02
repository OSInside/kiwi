from mock import patch
from pytest import raises

from kiwi.system.root_import import RootImport

from kiwi.exceptions import KiwiRootImportError


class TestRootImport:
    @patch('kiwi.system.root_import.RootImportOCI')
    def test_docker_import(self, mock_docker_import):
        RootImport('root_dir', 'file:///image.tar.xz', 'docker')
        mock_docker_import.assert_called_once_with(
            'root_dir', 'file:///image.tar.xz',
            custom_args={'archive_transport': 'docker-archive'}
        )

    @patch('kiwi.system.root_import.RootImportOCI')
    def test_oci_import(self, mock_oci_import):
        RootImport('root_dir', 'file:///image.tar.xz', 'oci')
        mock_oci_import.assert_called_once_with(
            'root_dir', 'file:///image.tar.xz',
            custom_args={'archive_transport': 'oci-archive'}
        )

    def test_not_implemented_import(self):
        with raises(KiwiRootImportError):
            RootImport('root_dir', 'file:///image.tar.xz', 'foo')
