from unittest.mock import (
    patch, Mock
)

from kiwi.container.wsl import ContainerImageWsl


class TestContainerImageWsl:
    def setup(self):
        self.wsl = ContainerImageWsl('root_dir')

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.container.wsl.ArchiveTar')
    @patch('kiwi.container.wsl.Compress')
    @patch('kiwi.container.wsl.Defaults.get_exclude_list_for_root_data_sync')
    @patch('kiwi.container.wsl.Defaults.get_exclude_list_from_custom_exclude_files')
    @patch('kiwi.container.wsl.Command.run')
    def test_create(
        self, mock_Command_run,
        mock_get_exclude_list_from_custom_exclude_files,
        mock_get_exclude_list_for_root_data_sync,
        mock_Compress, mock_ArchiveTar
    ):
        archive = Mock()
        mock_ArchiveTar.return_value = archive
        compress = Mock()
        mock_Compress.return_value = compress

        self.wsl.create('target_dir/image.wsl')
        mock_ArchiveTar.assert_called_once_with(
            'target_dir/image.wsl'
        )
        archive.create.assert_called_once_with(
            'root_dir',
            exclude=mock_get_exclude_list_for_root_data_sync.
            return_value + mock_get_exclude_list_from_custom_exclude_files.
            return_value,
            options=['--numeric-owner', '--absolute-names']
        )
        mock_Compress.assert_called_once_with(
            archive.create.return_value
        )
        compress.gzip.assert_called_once_with()
        mock_Command_run.assert_called_once_with(
            ['mv', compress.gzip.return_value, 'target_dir/image.wsl']
        )
