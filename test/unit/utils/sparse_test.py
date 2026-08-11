from unittest.mock import patch

from kiwi.utils.sparse import SparseFile


class TestSparseFile:
    @patch('kiwi.utils.sparse.Path.which')
    @patch('kiwi.utils.sparse.Command.run')
    def test_create_with_qemu_img(self, mock_command_run, mock_which):
        mock_which.return_value = '/usr/bin/qemu-img'
        SparseFile.create('disk.raw', '20M')
        mock_command_run.assert_called_once_with(
            ['qemu-img', 'create', 'disk.raw', '20M']
        )

    @patch('kiwi.utils.sparse.Path.which')
    @patch('kiwi.utils.sparse.Command.run')
    def test_create_with_dd_fallback(self, mock_command_run, mock_which):
        mock_which.return_value = None
        SparseFile.create('disk.raw', '20M')
        mock_command_run.assert_called_once_with(
            [
                'dd', 'if=/dev/null', 'of=disk.raw',
                'bs=1', 'count=0', 'seek=20M'
            ]
        )
