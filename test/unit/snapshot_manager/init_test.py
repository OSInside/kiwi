from unittest.mock import (
    patch, Mock
)
from pytest import raises

from kiwi.snapshot_manager import SnapshotManager

from kiwi.exceptions import KiwiSnapshotManagerSetupError


class TestSnapshotManager:
    def test_snapshot_manager_not_implemented(self):
        with raises(KiwiSnapshotManagerSetupError):
            SnapshotManager.new(
                'foo', '/dev/device', 'root_dir', 'mountpoint', '@', [Mock()]
            )

    @patch('kiwi.snapshot_manager.snapper.SnapshotManagerSnapper')
    def test_snapshot_manager_snapper(self, mock_snapper):
        SnapshotManager.new(
            'snapper', '/dev/device', 'root_dir', 'mountpoint', '@', None
        )
        mock_snapper.assert_called_once_with(
            '/dev/device', 'root_dir', 'mountpoint', '@', None
        )
