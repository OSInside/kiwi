import mock
from mock import patch
from mock import call

from .test_helper import raises

from kiwi.system.uri import Uri
from kiwi.system.root_import.oci import RootImportOCI
from kiwi.exceptions import KiwiRootImportError


class TestRootImportOCI(object):
    @patch('os.path.exists')
    @patch('kiwi.system.root_import.oci.mkdtemp')
    def setup(self, mock_mkdtemp, mock_path):
        mock_path.return_value = True
        tmpdirs = ['kiwi_unpack_dir', 'kiwi_layout_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp
        with patch.dict('os.environ', {'HOME': '../data'}):
            self.oci_import = RootImportOCI(
                'root_dir', Uri('file:///image.tar.xz#tag')
            )
        assert self.oci_import.image_file == '/image.tar.xz'

    @patch('os.path.exists')
    @raises(KiwiRootImportError)
    def test_failed_init(self, mock_path):
        mock_path.return_value = False
        RootImportOCI(
            'root_dir', Uri('file:///image.tar.xz')
        )

    @patch('kiwi.system.root_import.oci.ArchiveTar')
    @patch('kiwi.system.root_import.base.Checksum')
    @patch('kiwi.system.root_import.oci.Path.create')
    @patch('kiwi.system.root_import.oci.Command.run')
    @patch('kiwi.system.root_import.oci.DataSync')
    @patch('kiwi.system.root_import.oci.mkdtemp')
    def test_sync_data(
        self, mock_mkdtemp, mock_sync, mock_run,
        mock_path, mock_md5, mock_tar
    ):
        mock_mkdtemp.return_value = 'kiwi_uncompressed'
        extract = mock.Mock()
        mock_tar.extract = extract
        sync = mock.Mock()
        mock_sync.return_value = sync
        md5 = mock.Mock()
        mock_md5.return_value = mock.Mock()

        self.oci_import.sync_data()

        mock_tar.extract.called_once_with('kiwi_uncompressed')

        assert mock_run.call_args_list == [
            call([
                'skopeo', 'copy', 'oci:kiwi_uncompressed:tag',
                'oci:kiwi_layout_dir:base_layer'
            ]),
            call([
                'umoci', 'unpack', '--image',
                'kiwi_layout_dir:base_layer', 'kiwi_unpack_dir'
            ])
        ]

        mock_sync.assert_called_once_with(
            'kiwi_unpack_dir/rootfs/', 'root_dir/'
        )
        sync.sync_data.assert_called_once_with(
            options=['-a', '-H', '-X', '-A']
        )
        mock_md5.assert_called_once_with('root_dir/image/imported_root')
        md5.md5.called_once_with('root_dir/image/imported_root.md5')
        assert mock_tar.call_args_list == [
            call('/image.tar.xz'), call('root_dir/image/imported_root')
        ]

    @patch('kiwi.command.Command.run')
    @patch('kiwi.system.root_import.oci.log.warning')
    def test_extract_oci_image_unknown_uri(self, mock_warn, mock_run):
        self.oci_import.unknown_uri = 'oci://some_image'
        self.oci_import.extract_oci_image()
        mock_run.assert_called_once_with([
            'skopeo', 'copy', 'oci://some_image',
            'oci:kiwi_layout_dir:base_layer'
        ])
        assert mock_warn.called

    @patch('kiwi.system.root_import.oci.ArchiveTar')
    @patch('os.path.exists')
    @patch('kiwi.system.root_import.oci.mkdtemp')
    @patch('kiwi.command.Command.run')
    def test_extract_oci_image_without_tag(
        self, mock_run, mock_mkdtemp, mock_path, mock_tar
    ):
        mock_path.return_value = True
        tmpdirs = ['kiwi_uncompressed', 'kiwi_unpack_dir', 'kiwi_layout_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp
        with patch.dict('os.environ', {'HOME': '../data'}):
            oci_import = RootImportOCI(
                'root_dir', Uri('file:///image.tar.xz')
            )
        oci_import.extract_oci_image()
        mock_run.assert_called_once_with([
            'skopeo', 'copy', 'oci:kiwi_uncompressed',
            'oci:kiwi_layout_dir:base_layer'
        ])
        mock_tar.assert_called_once_with('/image.tar.xz')

    @patch('kiwi.system.root_import.oci.Path.wipe')
    def test_del(self, mock_path):
        self.oci_import.oci_layout_dir = 'layout_dir'
        self.oci_import.oci_unpack_dir = 'unpack_dir'
        self.oci_import.uncompressed_image = 'uncompressed_file'
        self.oci_import.__del__()

        assert mock_path.call_args_list == [
            call('layout_dir'), call('unpack_dir'), call('uncompressed_file')
        ]
