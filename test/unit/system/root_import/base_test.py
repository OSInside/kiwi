from mock import (
    patch, call
)
from pytest import raises

from kiwi.system.uri import Uri
from kiwi.system.root_import.base import RootImportBase

from kiwi.exceptions import KiwiRootImportError


class TestRootImportBase:
    @patch('os.path.exists')
    @patch('kiwi.system.uri.Defaults.is_buildservice_worker')
    def test_init(self, mock_buildservice, mock_path):
        mock_buildservice.return_value = False
        mock_path.return_value = True
        with patch.dict('os.environ', {'HOME': '../data'}):
            RootImportBase('root_dir', Uri('file:///image.tar.xz'))
        assert call('/image.tar.xz') in mock_path.call_args_list

    def test_init_remote_uri(self):
        with raises(KiwiRootImportError):
            RootImportBase('root_dir', Uri('http://example.com/image.tar.xz'))

    @patch('kiwi.system.root_import.base.log.warning')
    def test_init_unknown_uri(self, mock_log_warn):
        root = RootImportBase('root_dir', Uri('docker://opensuse:leap'))
        assert root.unknown_uri == 'docker://opensuse:leap'
        assert mock_log_warn.called

    @patch('os.path.exists')
    def test_init_non_existing(self, mock_path):
        mock_path.return_value = False
        with patch.dict('os.environ', {'HOME': '../data'}):
            with raises(KiwiRootImportError):
                RootImportBase('root_dir', Uri('file:///image.tar.xz'))

    @patch('os.path.exists')
    def test_data_sync(self, mock_path):
        mock_path.return_value = True
        with patch.dict('os.environ', {'HOME': '../data'}):
            root_import = RootImportBase(
                'root_dir', Uri('file:///image.tar.xz')
            )
        with raises(NotImplementedError):
            root_import.sync_data()
