from mock import patch

from .test_helper import raises

from kiwi.system.uri import Uri
from kiwi.system.root_import.base import RootImportBase
from kiwi.exceptions import KiwiRootImportError


class TestRootImportBase(object):
    @patch('os.path.exists')
    def test_init(self, mock_path):
        mock_path.return_value = True
        RootImportBase('root_dir', Uri('file:///image.tar.xz'))
        mock_path.assert_called_once_with('/image.tar.xz')

    @raises(KiwiRootImportError)
    def test_init_remote_uri(self):
        RootImportBase('root_dir', Uri('http://example.com/image.tar.xz'))

    @patch('kiwi.system.root_import.base.log.warning')
    def test_init_unknown_uri(self, mock_log_warn):
        root = RootImportBase('root_dir', Uri('docker://opensuse:leap'))
        assert root.unknown_uri == 'docker://opensuse:leap'
        assert mock_log_warn.called

    @patch('os.path.exists')
    @raises(KiwiRootImportError)
    def test_init_non_existing(self, mock_path):
        mock_path.return_value = False
        RootImportBase('root_dir', Uri('file:///image.tar.xz'))
        mock_path.assert_called_once_with('/image.tar.xz')

    @raises(NotImplementedError)
    @patch('os.path.exists')
    def test_data_sync(self, mock_path):
        mock_path.return_value = True
        root_import = RootImportBase('root_dir', Uri('file:///image.tar.xz'))
        root_import.sync_data()
