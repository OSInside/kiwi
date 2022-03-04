import io
from mock import (
    patch, Mock, MagicMock, call
)

from kiwi.utils.veritysetup import VeritySetup


class TestVeritySetup:
    @patch('os.path.getsize')
    def setup(self, mock_os_path_getsize):
        mock_os_path_getsize.return_value = 42
        self.veritysetup = VeritySetup('image_file', data_blocks=10)
        self.veritysetup_full = VeritySetup('image_file')

    @patch('os.path.getsize')
    def setup_method(self, cls, mock_os_path_getsize):
        self.setup()

    @patch('kiwi.utils.veritysetup.Command.run')
    def test_format(self, mock_Command_run):
        self.veritysetup.format()
        mock_Command_run.assert_called_once_with(
            [
                'veritysetup', 'format', 'image_file', 'image_file',
                '--no-superblock', '--hash-offset=42', '--data-blocks=10'
            ]
        )

    @patch('kiwi.utils.veritysetup.Command.run')
    def test_format_full(self, mock_Command_run):
        self.veritysetup_full.format()
        mock_Command_run.assert_called_once_with(
            [
                'veritysetup', 'format', 'image_file', 'image_file',
                '--no-superblock', '--hash-offset=42'
            ]
        )

    def test_store_credentials(self):
        self.veritysetup.verity_call = Mock()
        target_block_id = Mock()
        target_block_id.get_blkid.return_value = 'uuid'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.veritysetup.store_credentials(
                'credentials_file', target_block_id
            )
        assert file_handle.write.call_args_list == [
            call(self.veritysetup.verity_call.output.strip.return_value),
            call('\n'),
            call("PARTUUID: uuid"),
            call('\n'),
            call('Root hashoffset: 42'),
            call('\n'),
            call('Superblock: --no-superblock'),
            call('\n')
        ]
