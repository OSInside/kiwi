import os
import errno
import logging
from pytest import fixture
from stat import ST_MODE
from unittest.mock import (
    patch, Mock
)

from kiwi.utils.sync import DataSync


class TestDataSync:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        self.sync = DataSync('source_dir', 'target_dir')

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.utils.sync.RuntimeConfig')
    @patch('kiwi.utils.sync.Command.run')
    @patch('kiwi.utils.sync.DataSync.target_supports_extended_attributes')
    @patch('os.chmod')
    @patch('os.stat')
    def test_sync_data(
        self, mock_stat, mock_chmod, mock_xattr_support, mock_command,
        mock_RuntimeConfig
    ):
        mock_RuntimeConfig.return_value.get_sync_sparse.return_value = False
        mock_stat.return_value = os.stat('.')
        mock_xattr_support.return_value = False
        with self._caplog.at_level(logging.WARNING):
            self.sync.sync_data(
                options=[
                    '--archive', '--hard-links', '--xattrs',
                    '--acls', '--one-file-system'
                ],
                exclude=['exclude_me']
            )
            mock_command.assert_called_once_with(
                [
                    'rsync', '--archive', '--hard-links', '--one-file-system',
                    '--exclude', '/exclude_me', 'source_dir', 'target_dir'
                ]
            )
            mock_chmod.assert_called_once_with(
                'target_dir', mock_stat.return_value[ST_MODE]
            )

    @patch('kiwi.utils.sync.RuntimeConfig')
    @patch('kiwi.utils.sync.DataSync._rsync_supports_sparse_inplace')
    @patch('kiwi.utils.sync.Command.run')
    @patch('kiwi.utils.sync.DataSync.target_supports_extended_attributes')
    @patch('os.chmod')
    @patch('os.stat')
    def test_sync_data_sparse(
        self, mock_stat, mock_chmod, mock_xattr_support, mock_command,
        mock_sparse_inplace, mock_RuntimeConfig
    ):
        mock_RuntimeConfig.return_value.get_sync_sparse.return_value = True
        mock_sparse_inplace.return_value = True
        mock_xattr_support.return_value = True
        mock_stat.return_value = os.stat('.')
        self.sync.sync_data(options=['--archive', '--inplace'])
        mock_command.assert_called_once_with(
            [
                'rsync', '--archive', '--inplace', '--sparse',
                'source_dir', 'target_dir'
            ]
        )

    @patch('kiwi.utils.sync.RuntimeConfig')
    @patch('kiwi.utils.sync.Command.run')
    @patch('kiwi.utils.sync.DataSync.target_supports_extended_attributes')
    @patch('os.chmod')
    @patch('os.stat')
    def test_sync_data_sparse_already_requested(
        self, mock_stat, mock_chmod, mock_xattr_support, mock_command,
        mock_RuntimeConfig
    ):
        mock_RuntimeConfig.return_value.get_sync_sparse.return_value = True
        mock_xattr_support.return_value = True
        mock_stat.return_value = os.stat('.')
        self.sync.sync_data(options=['--archive', '--sparse'])
        mock_command.assert_called_once_with(
            ['rsync', '--archive', '--sparse', 'source_dir', 'target_dir']
        )

    @patch('kiwi.utils.sync.RuntimeConfig')
    @patch('kiwi.utils.sync.Command.run')
    @patch('kiwi.utils.sync.DataSync.target_supports_extended_attributes')
    @patch('os.chmod')
    @patch('os.stat')
    def test_sync_data_sparse_skipped_for_preallocate(
        self, mock_stat, mock_chmod, mock_xattr_support, mock_command,
        mock_RuntimeConfig
    ):
        mock_RuntimeConfig.return_value.get_sync_sparse.return_value = True
        mock_xattr_support.return_value = True
        mock_stat.return_value = os.stat('.')
        with self._caplog.at_level(logging.WARNING):
            self.sync.sync_data(options=['--archive', '--preallocate'])
            assert 'incompatible with --preallocate' in self._caplog.text
        mock_command.assert_called_once_with(
            ['rsync', '--archive', '--preallocate', 'source_dir', 'target_dir']
        )

    @patch('kiwi.utils.sync.RuntimeConfig')
    @patch('kiwi.utils.sync.DataSync._rsync_supports_sparse_inplace')
    @patch('kiwi.utils.sync.Command.run')
    @patch('kiwi.utils.sync.DataSync.target_supports_extended_attributes')
    @patch('os.chmod')
    @patch('os.stat')
    def test_sync_data_sparse_skipped_for_old_rsync(
        self, mock_stat, mock_chmod, mock_xattr_support, mock_command,
        mock_sparse_inplace, mock_RuntimeConfig
    ):
        mock_RuntimeConfig.return_value.get_sync_sparse.return_value = True
        mock_sparse_inplace.return_value = False
        mock_xattr_support.return_value = True
        mock_stat.return_value = os.stat('.')
        with self._caplog.at_level(logging.WARNING):
            self.sync.sync_data(options=['--archive', '--inplace'])
            assert 'rsync too old' in self._caplog.text
        mock_command.assert_called_once_with(
            ['rsync', '--archive', '--inplace', 'source_dir', 'target_dir']
        )

    @patch('kiwi.utils.sync.Command.run')
    def test_rsync_supports_sparse_inplace(self, mock_command):
        mock_command.return_value = Mock(
            output='rsync  version 3.4.0  protocol version 32'
        )
        assert DataSync._rsync_supports_sparse_inplace() is True
        mock_command.return_value = Mock(
            output='rsync  version 3.1.2  protocol version 31'
        )
        assert DataSync._rsync_supports_sparse_inplace() is False
        mock_command.return_value = Mock(output='no version information')
        assert DataSync._rsync_supports_sparse_inplace() is False

    @patch('kiwi.utils.sync.Command.run')
    def test_rsync_supports_sparse_inplace_detection_failed(
        self, mock_command
    ):
        mock_command.side_effect = Exception('rsync not found')
        with self._caplog.at_level(logging.WARNING):
            assert DataSync._rsync_supports_sparse_inplace() is False
            assert 'Could not detect rsync version' in self._caplog.text

    @patch('kiwi.utils.sync.RuntimeConfig')
    @patch('kiwi.utils.sync.Command.run')
    @patch('os.chmod')
    @patch('os.stat')
    def test_sync_data_force_trailing_slash(
        self, mock_stat, mock_chmod, mock_command, mock_RuntimeConfig
    ):
        mock_RuntimeConfig.return_value.get_sync_sparse.return_value = False
        mock_stat.return_value = os.stat('.')
        self.sync.sync_data(force_trailing_slash=True)
        mock_command.assert_called_once_with(
            ['rsync', 'source_dir/', 'target_dir']
        )

    @patch('os.getxattr')
    def test_target_supports_extended_attributes(self, mock_getxattr):
        assert self.sync.target_supports_extended_attributes() is True
        mock_getxattr.assert_called_once_with(
            'target_dir', 'user.mime_type'
        )

    @patch('os.getxattr')
    def test_target_does_not_support_extended_attributes(self, mock_getxattr):
        effect = OSError()
        effect.errno = errno.ENOTSUP
        mock_getxattr.side_effect = effect
        assert self.sync.target_supports_extended_attributes() is False
        effect = NotImplemented
        mock_getxattr.side_effect = effect
        assert self.sync.target_supports_extended_attributes() is True
