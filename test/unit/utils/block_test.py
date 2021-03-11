from mock import patch

from kiwi.utils.block import BlockID


class TestBlockID:
    def setup(self):
        self.blkid = BlockID('device')

    @patch('kiwi.utils.block.Command.run')
    def test_setup_with_uuid_format(self, mock_command):
        BlockID('UUID=uuid')
        mock_command.assert_called_once_with(
            ['blkid', '--uuid', 'uuid']
        )

    @patch('kiwi.utils.block.Command.run')
    def test_get_blkid(self, mock_command):
        self.blkid.get_blkid('LABEL')
        mock_command.assert_called_once_with(
            ['blkid', 'device', '-s', 'LABEL', '-o', 'value']
        )

    @patch('kiwi.utils.block.BlockID.get_blkid')
    def test_get_filesystem(self, mock_get_blkid):
        self.blkid.get_filesystem()
        mock_get_blkid.assert_called_once_with('TYPE')

    @patch('kiwi.utils.block.BlockID.get_blkid')
    def test_get_label(self, mock_get_blkid):
        self.blkid.get_label()
        mock_get_blkid.assert_called_once_with('LABEL')

    @patch('kiwi.utils.block.BlockID.get_blkid')
    def test_get_uuid(self, mock_get_blkid):
        self.blkid.get_uuid()
        mock_get_blkid.assert_called_once_with('UUID')
