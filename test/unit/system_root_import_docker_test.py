import mock
from mock import patch
from mock import call

from kiwi.system.root_import.docker import RootImportDocker


class TestRootImportDocker(object):
    @patch('os.path.exists')
    def setup(self, mock_path):
        mock_path.return_value = True
        self.docker_import = RootImportDocker(
            'root_dir', 'file:///image.tar.xz'
        )
        assert self.docker_import.image_file == '/image.tar.xz'

    @patch('kiwi.system.root_import.docker.Compress')
    @patch('kiwi.system.root_import.docker.Command.run')
    @patch('kiwi.system.root_import.docker.DataSync')
    @patch('kiwi.system.root_import.docker.mkdtemp')
    def test_sync_data(
        self, mock_mkdtemp, mock_sync, mock_run, mock_compress
    ):
        uncompress = mock.Mock()
        uncompress.uncompressed_filename = 'tmp_uncompressed'
        mock_compress.return_value = uncompress

        tmpdirs = ['kiwi_unpack_dir', 'kiwi_layout_dir']

        def call_mkdtemp(prefix):
            return tmpdirs.pop()

        mock_mkdtemp.side_effect = call_mkdtemp

        sync = mock.Mock()
        mock_sync.return_value = sync

        self.docker_import.sync_data()

        mock_compress.assert_called_once_with('/image.tar.xz')
        uncompress.uncompress.assert_called_once_with(True)

        assert mock_run.call_args_list == [
            call([
                'skopeo', 'copy', 'docker-archive:tmp_uncompressed',
                'oci:kiwi_layout_dir'
            ]),
            call([
                'umoci', 'unpack', '--image',
                'kiwi_layout_dir', 'kiwi_unpack_dir'
            ])
        ]

        mock_sync.assert_called_once_with(
            'kiwi_unpack_dir/rootfs/', 'root_dir/'
        )
        sync.sync_data.assert_called_once_with(
            options=['-a', '-H', '-X', '-A']
        )

    @patch('kiwi.system.root_import.docker.Path.wipe')
    def test_del(self, mock_path):
        self.docker_import.oci_layout_dir = 'layout_dir'
        self.docker_import.oci_unpack_dir = 'unpack_dir'
        self.docker_import.uncompressed_image = 'uncompressed_file'
        self.docker_import.__del__()

        assert mock_path.call_args_list == [
            call('layout_dir'), call('unpack_dir'), call('uncompressed_file')
        ]
