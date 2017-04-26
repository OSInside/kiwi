import mock
from mock import patch

from kiwi.system.uri import Uri
from kiwi.system.root_import.docker import RootImportDocker


class TestRootImportDocker(object):

    @patch('os.path.exists')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_import.docker.Compress')
    @patch('kiwi.system.root_import.oci.mkdtemp')
    def test_extract_oci_image(
        self, mock_mkdtemp, mock_compress, mock_run, mock_exists
    ):
        mock_exists.return_value = True
        uncompress = mock.Mock()
        uncompress.uncompressed_filename = 'tmp_uncompressed'
        mock_compress.return_value = uncompress
        tmpdirs = ['kiwi_unpack_dir', 'kiwi_layout_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp

        docker_import = RootImportDocker(
            'root_dir', Uri('file:///image.tar.xz')
        )
        docker_import.extract_oci_image()
        mock_compress.assert_called_once_with('/image.tar.xz')
        uncompress.uncompress.assert_called_once_with(True)
        mock_run.assert_called_once_with([
            'skopeo', 'copy', 'docker-archive:tmp_uncompressed',
            'oci:kiwi_layout_dir'
        ])

    @patch('os.path.exists')
    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_import.oci.mkdtemp')
    @patch('kiwi.system.root_import.base.log.warning')
    def test_extract_oci_image_unknown_uri(
        self, mock_warn, mock_mkdtemp, mock_run, mock_exists
    ):
        mock_exists.return_value = True
        tmpdirs = ['kiwi_unpack_dir', 'kiwi_layout_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp

        docker_import = RootImportDocker(
            'root_dir', Uri('docker://opensuse')
        )
        docker_import.extract_oci_image()
        mock_run.assert_called_once_with([
            'skopeo', 'copy', 'docker://opensuse',
            'oci:kiwi_layout_dir'
        ])
        assert mock_warn.called
