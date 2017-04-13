from mock import patch

from .test_helper import raises

from kiwi.system.root_import import RootImport
from kiwi.exceptions import KiwiRootImportError


class TestRootImport(object):
    @patch('kiwi.system.root_import.RootImportDocker')
    def test_docker_import(self, mock_docker_import):
        RootImport('root_dir', 'file:///image.tar.xz', 'docker')
        mock_docker_import.assert_called_once_with(
            'root_dir', 'file:///image.tar.xz'
        )

    @patch('kiwi.system.root_import.RootImportOCI')
    def test_oci_import(self, mock_oci_import):
        RootImport('root_dir', 'file:///image.tar.xz', 'oci')
        mock_oci_import.assert_called_once_with(
            'root_dir', 'file:///image.tar.xz'
        )

    @raises(KiwiRootImportError)
    def test_not_implemented_import(self):
        RootImport('root_dir', 'file:///image.tar.xz', 'foo')
