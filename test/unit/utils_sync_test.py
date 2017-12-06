import os
from stat import ST_MODE
from mock import patch

from kiwi.utils.sync import DataSync


class TestDataSync(object):
    def setup(self):
        self.sync = DataSync('source_dir', 'target_dir')

    @patch('kiwi.utils.sync.Command.run')
    @patch('kiwi.utils.sync.DataSync.target_supports_extended_attributes')
    @patch('kiwi.logger.log.warning')
    @patch('os.chmod')
    @patch('os.stat')
    def test_sync_data(
        self, mock_stat, mock_chmod, mock_warn, mock_xattr_support, mock_command
    ):
        mock_stat.return_value = os.stat('.')
        mock_xattr_support.return_value = False
        self.sync.sync_data(
            options=['-a', '-H', '-X', '-A', '--one-file-system'],
            exclude=['exclude_me']
        )
        mock_command.assert_called_once_with(
            [
                'rsync', '-a', '-H', '--one-file-system',
                '--exclude', '/exclude_me', 'source_dir', 'target_dir'
            ]
        )
        mock_chmod.assert_called_once_with(
            'target_dir', mock_stat.return_value[ST_MODE]
        )
        assert mock_warn.called

    @patch('xattr.getxattr')
    def test_target_supports_extended_attributes(self, mock_getxattr):
        assert self.sync.target_supports_extended_attributes() is True
        mock_getxattr.assert_called_once_with(
            'target_dir', 'user.mime_type'
        )

    @patch('xattr.getxattr')
    def test_target_does_not_support_extended_attributes(self, mock_getxattr):
        mock_getxattr.side_effect = OSError(
            """[Errno 95] Operation not supported: b'/boot/efi"""
        )
        assert self.sync.target_supports_extended_attributes() is False
