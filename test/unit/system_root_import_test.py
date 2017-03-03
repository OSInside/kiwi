import mock
from mock import patch
from mock import call

from .test_helper import *

from kiwi.system.root_import import RootImport
from kiwi.exceptions import KiwiRootImportError

class TestRootImport(object):
    @patch('os.path.exists') 
    def test_init(self, mock_path):
        mock_path.return_value = True
        xml_state = mock.Mock()
        root_import = RootImport(xml_state, 'root_dir', 'file:///image.tar.xz')
        assert(root_import.base_image == '/image.tar.xz')

    @raises(KiwiRootImportError)
    def test_init_remote_uri(self):
        xml_state = mock.Mock()
        RootImport(xml_state, 'root_dir', 'http://example.com/image.tar.xz')

    @raises(KiwiRootImportError)
    @patch('os.path.exists')
    def test_init_non_existing_image(self, mock_path):
        mock_path.return_value = False
        xml_state = mock.Mock()
        RootImport(xml_state, 'root_dir', 'file:///image.tar.xz')

    @patch('os.path.exists')
    @patch('kiwi.system.root_import.ContainerImage')
    @patch('kiwi.path.Path.create')
    @patch('shutil.copy')
    def test_sync_data(
        self, mock_copy, mock_path, mock_container, mock_path_exists
    ):
        xml_state = mock.Mock()
        container = mock.Mock()
        mock_container.return_value = container
        mock_path_exists.return_value = True

        root_import = RootImport(xml_state, 'root_dir', 'file:///image.tar.xz')
        root_import.sync_data()

        mock_path.assert_called_once_with('root_dir/image')
        mock_copy.assert_called_once_with('/image.tar.xz', 'root_dir/image')
        xml_state.build_type.set_derived_from.assert_called_once_with(
            'file://image/image.tar.xz'
        )

