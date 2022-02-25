import logging
from mock import (
    patch, Mock
)
from pytest import (
    raises, fixture
)

from kiwi.system.uri import Uri
from kiwi.system.root_import.oci import RootImportOCI

from kiwi.exceptions import KiwiRootImportError


class TestRootImportOCI:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    def setup(self, mock_path):
        mock_path.return_value = True
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.oci_import = RootImportOCI(
                'root_dir', Uri('file:///image.tar'),
                {'archive_transport': 'oci-archive'}
            )
        assert self.oci_import.image_file == '/image.tar'

    @patch('os.path.exists')
    def test_failed_init(self, mock_path):
        mock_path.return_value = False
        with raises(KiwiRootImportError):
            RootImportOCI(
                'root_dir', Uri('file:///image.tar.xz'),
                {'archive_transport': 'oci-archive'}
            )

    @patch('kiwi.system.root_import.oci.Compress')
    @patch('kiwi.system.root_import.base.Checksum')
    @patch('kiwi.system.root_import.oci.Path.create')
    @patch('kiwi.system.root_import.oci.OCI')
    def test_sync_data(self, mock_OCI, mock_path, mock_md5, mock_compress):
        oci = Mock()
        mock_OCI.new.return_value = oci
        md5 = Mock()
        mock_md5.return_value = Mock()

        uncompress = Mock()
        uncompress.get_format = Mock(return_value=None)
        mock_compress.return_value = uncompress

        self.oci_import.sync_data()

        mock_OCI.new.assert_called_once_with()

        oci.unpack.assert_called_once_with()
        oci.import_rootfs.assert_called_once_with(
            'root_dir'
        )
        mock_md5.assert_called_once_with('root_dir/image/imported_root')
        md5.md5.called_once_with('root_dir/image/imported_root.md5')
        uncompress.get_format.assert_called_once_with()

    @patch('kiwi.system.root_import.oci.Compress')
    @patch('kiwi.system.root_import.base.Checksum')
    @patch('kiwi.system.root_import.oci.Path.create')
    @patch('kiwi.system.root_import.oci.OCI')
    def test_sync_data_compressed_image(
        self, mock_OCI, mock_path, mock_md5, mock_compress
    ):
        oci = Mock()
        mock_OCI.new.return_value = oci
        md5 = Mock()
        mock_md5.return_value = Mock()

        uncompress = Mock()
        uncompress.get_format = Mock(return_value='xz')
        mock_compress.return_value = uncompress

        self.oci_import.sync_data()

        mock_OCI.new.assert_called_once_with()

        oci.unpack.assert_called_once_with()
        oci.import_rootfs.assert_called_once_with(
            'root_dir'
        )
        mock_md5.assert_called_once_with('root_dir/image/imported_root')
        md5.md5.called_once_with('root_dir/image/imported_root.md5')
        uncompress.get_format.assert_called_once_with()
        uncompress.uncompress.assert_called_once_with(True)

    @patch('os.path.exists')
    @patch('kiwi.system.root_import.base.Checksum')
    @patch('kiwi.system.root_import.oci.Path.create')
    @patch('kiwi.system.root_import.oci.OCI')
    def test_sync_data_unknown_uri(
        self, mock_OCI, mock_path, mock_md5, mock_exists
    ):
        mock_exists.return_value = True
        oci = Mock()
        mock_OCI.new.return_value = oci
        md5 = Mock()
        mock_md5.return_value = Mock()
        with patch.dict('os.environ', {'HOME': '../data'}):
            oci_import = RootImportOCI(
                'root_dir', Uri('docker:image:tag'),
                {'archive_transport': 'docker-archive'}
            )

        with self._caplog.at_level(logging.WARNING):
            oci_import.sync_data()
            mock_OCI.new.assert_called_once_with()
            oci.import_container_image.assert_called_once_with(
                'docker:image:tag'
            )
            oci.unpack.assert_called_once_with()
            oci.import_rootfs.assert_called_once_with(
                'root_dir'
            )
            mock_md5.assert_called_once_with('root_dir/image/imported_root')
            md5.md5.called_once_with('root_dir/image/imported_root.md5')
