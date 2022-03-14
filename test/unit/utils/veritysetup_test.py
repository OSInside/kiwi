import io
from textwrap import dedent
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
        self.verity_dict = {
            'UUID': '',
            'Hashtype': '1',
            'Datablocks': '10',
            'Datablocksize': '4096',
            'Hashblocksize': '4096',
            'Hashalgorithm': 'sha256',
            'Salt': 'fb074d1db50...',
            'Roothash': 'e2728628377...'
        }

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
        verity_call = Mock()
        verity_call.output = dedent('''\n
            VERITY header information for mysquash.img
            UUID:
            Hash type:          1
            Data blocks:        10
            Data block size:    4096
            Hash block size:    4096
            Hash algorithm:     sha256
            Salt:               fb074d1db50...
            Root hash:          e2728628377...
        ''')
        mock_Command_run.return_value = verity_call
        assert self.veritysetup_full.format() == self.verity_dict
        mock_Command_run.assert_called_once_with(
            [
                'veritysetup', 'format', 'image_file', 'image_file',
                '--no-superblock', '--hash-offset=42'
            ]
        )

    def test_store_credentials(self):
        self.veritysetup.verity_call = Mock()
        self.veritysetup.verity_dict = self.verity_dict
        target_block_id = Mock()
        target_block_id.get_blkid.return_value = 'uuid'
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.veritysetup.store_credentials(
                'credentials_file', target_block_id
            )
        assert file_handle.write.call_args_list == [
            call('Datablocks: 10\n'),
            call('Datablocksize: 4096\n'),
            call('Hashalgorithm: sha256\n'),
            call('Hashblocksize: 4096\n'),
            call('Hashtype: 1\n'),
            call('Roothash: e2728628377...\n'),
            call('Salt: fb074d1db50...\n'),
            call('UUID: \n'),
            call('PARTUUID: uuid'),
            call('\n'),
            call('Root hashoffset: 42'),
            call('\n'),
            call('Superblock: --no-superblock'),
            call('\n')
        ]

    @patch('kiwi.utils.veritysetup.BlockID')
    def test_get_block_storage_filesystem(self, mock_BlockID):
        block_id = Mock()
        mock_BlockID.return_value = block_id
        block_id.get_filesystem.return_value = 'ext3'
        assert self.veritysetup.get_block_storage_filesystem() == 'ext3'
        block_id.get_filesystem.side_effect = Exception
        assert self.veritysetup.get_block_storage_filesystem() == ''
