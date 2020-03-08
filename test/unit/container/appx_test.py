import io
from pytest import raises
from mock import (
    patch, Mock, MagicMock, call
)

from kiwi.container.appx import ContainerImageAppx
from kiwi.exceptions import KiwiContainerSetupError


class TestContainerImageAppx:
    @patch('kiwi.container.appx.RuntimeConfig')
    @patch('os.path.exists')
    def setup(self, mock_os_path_exists, mock_RuntimeConfig):
        mock_os_path_exists.return_value = True
        self.appx = ContainerImageAppx(
            'root_dir', {
                'metadata_path': 'meta/data'
            }
        )

    @patch('kiwi.container.appx.RuntimeConfig')
    @patch('os.path.exists')
    def test_init_raises(self, mock_os_path_exists, mock_RuntimeConfig):
        mock_os_path_exists.return_value = True
        with raises(KiwiContainerSetupError):
            ContainerImageAppx('root_dir', custom_args=None)
        mock_os_path_exists.return_value = False
        with raises(KiwiContainerSetupError):
            ContainerImageAppx(
                'root_dir', custom_args={
                    'metadata_path': 'meta/data'
                }
            )

    @patch('kiwi.container.appx.ArchiveTar')
    @patch('kiwi.container.appx.Compress')
    @patch('kiwi.container.appx.Defaults.get_exclude_list_for_root_data_sync')
    @patch('kiwi.container.appx.NamedTemporaryFile')
    @patch('kiwi.container.appx.Command.run')
    @patch('os.walk')
    def test_create(
        self, mock_os_walk, mock_Command_run, mock_NamedTemporaryFile,
        mock_get_exclude_list_for_root_data_sync,
        mock_Compress, mock_ArchiveTar
    ):
        mock_os_walk.return_value = [
            ('source', ['bar', 'baz'], []),
            ('source/bar', [], []),
            ('source/baz', [], ['baz_file'])
        ]
        tempfile = Mock()
        tempfile.name = 'tempfile'
        mock_NamedTemporaryFile.return_value = tempfile
        archive = Mock()
        mock_ArchiveTar.return_value = archive
        compress = Mock()
        mock_Compress.return_value = compress
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.appx.create('target_dir/image.appx')
            assert file_handle.write.call_args_list == [
                call('[Files]\n'),
                call('"source/baz/baz_file" "baz_file"\n')
            ]
        mock_ArchiveTar.assert_called_once_with('meta/data/install.tar')
        archive.create.assert_called_once_with(
            'root_dir',
            exclude=mock_get_exclude_list_for_root_data_sync.return_value
        )
        mock_Compress.assert_called_once_with(
            archive.create.return_value
        )
        compress.gzip.assert_called_once_with()
        mock_Command_run.assert_called_once_with(
            ['appx', '-o', 'target_dir/image.appx', '-f', 'tempfile']
        )
