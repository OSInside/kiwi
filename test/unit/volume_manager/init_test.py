from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.volume_manager import VolumeManager

from kiwi.exceptions import KiwiVolumeManagerSetupError


class TestVolumeManager:
    def test_volume_manager_not_implemented(self):
        with raises(KiwiVolumeManagerSetupError):
            VolumeManager.new('foo', Mock(), 'root_dir', [Mock()])

    @patch('kiwi.volume_manager.lvm.VolumeManagerLVM')
    def test_volume_manager_lvm(self, mock_lvm):
        device_map = Mock()
        volumes = [Mock()]
        VolumeManager.new('lvm', device_map, 'root_dir', volumes)
        mock_lvm.assert_called_once_with(
            device_map, 'root_dir', volumes, None
        )

    @patch('kiwi.volume_manager.btrfs.VolumeManagerBtrfs')
    def test_volume_manager_btrfs(self, mock_btrfs):
        device_map = Mock()
        volumes = [Mock()]
        VolumeManager.new('btrfs', device_map, 'root_dir', volumes)
        mock_btrfs.assert_called_once_with(
            device_map, 'root_dir', volumes, None
        )
