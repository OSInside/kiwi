import mock
from mock import patch
# from mock import call

from .test_helper import raises

from kiwi.system.uri import Uri
from kiwi.system.root_import.oci import RootImportOCI
from kiwi.exceptions import KiwiRootImportError


class TestRootImportOCI(object):
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
    @raises(KiwiRootImportError)
    def test_failed_init(self, mock_path):
        mock_path.return_value = False
        RootImportOCI(
            'root_dir', Uri('file:///image.tar.xz'),
            {'archive_transport': 'oci-archive'}
        )

    @patch('kiwi.system.root_import.oci.Compress')
    @patch('kiwi.system.root_import.base.Checksum')
    @patch('kiwi.system.root_import.oci.Path.create')
    @patch('kiwi.system.root_import.oci.OCI')
    def test_sync_data(self, mock_OCI, mock_path, mock_md5, mock_compress):
        oci = mock.Mock()
        mock_OCI.return_value = oci
        md5 = mock.Mock()
        mock_md5.return_value = mock.Mock()

        uncompress = mock.Mock()
        uncompress.get_format = mock.Mock(return_value=None)
        mock_compress.return_value = uncompress

        self.oci_import.sync_data()

        mock_OCI.assert_called_once_with()

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
        oci = mock.Mock()
        mock_OCI.return_value = oci
        md5 = mock.Mock()
        mock_md5.return_value = mock.Mock()

        uncompress = mock.Mock()
        uncompress.get_format = mock.Mock(return_value='xz')
        mock_compress.return_value = uncompress

        self.oci_import.sync_data()

        mock_OCI.assert_called_once_with()

        oci.unpack.assert_called_once_with()
        oci.import_rootfs.assert_called_once_with(
            'root_dir'
        )
        mock_md5.assert_called_once_with('root_dir/image/imported_root')
        md5.md5.called_once_with('root_dir/image/imported_root.md5')
        uncompress.get_format.assert_called_once_with()
        uncompress.uncompress.assert_called_once_with(True)

    @patch('kiwi.logger.log.warning')
    @patch('os.path.exists')
    @patch('kiwi.system.root_import.base.Checksum')
    @patch('kiwi.system.root_import.oci.Path.create')
    @patch('kiwi.system.root_import.oci.OCI')
    def test_sync_data_unknown_uri(
        self, mock_OCI, mock_path, mock_md5, mock_exists, mock_warn
    ):
        mock_exists.return_value = True
        oci = mock.Mock()
        mock_OCI.return_value = oci
        md5 = mock.Mock()
        mock_md5.return_value = mock.Mock()
        with patch.dict('os.environ', {'HOME': '../data'}):
            oci_import = RootImportOCI(
                'root_dir', Uri('docker:image:tag'),
                {'archive_transport': 'docker-archive'}
            )

        oci_import.sync_data()

        mock_OCI.assert_called_once_with()

        oci.import_container_image.assert_called_once_with('docker:image:tag')
        oci.unpack.assert_called_once_with()
        oci.import_rootfs.assert_called_once_with(
            'root_dir'
        )
        mock_md5.assert_called_once_with('root_dir/image/imported_root')
        md5.md5.called_once_with('root_dir/image/imported_root.md5')
        assert mock_warn.called
