from mock import (
    patch, Mock
)
from pytest import raises

from kiwi.volume_manager import VolumeManager

from kiwi.exceptions import KiwiVolumeManagerSetupError


class TestVolumeManager:
    def test_volume_manager_not_implemented(self):
        with raises(KiwiVolumeManagerSetupError):
            VolumeManager('foo', Mock(), 'root_dir', Mock())

    @patch('kiwi.volume_manager.VolumeManagerLVM')
    @patch('os.path.exists')
    def test_volume_manager_lvm(self, mock_path, mock_lvm):
        mock_path.return_value = True
        provider = Mock()
        volumes = Mock()
        VolumeManager('lvm', provider, 'root_dir', volumes)
        mock_lvm.assert_called_once_with(
            provider, 'root_dir', volumes, None
        )

    @patch('kiwi.volume_manager.VolumeManagerBtrfs')
    @patch('os.path.exists')
    def test_volume_manager_btrfs(self, mock_path, mock_btrfs):
        mock_path.return_value = True
        provider = Mock()
        volumes = Mock()
        VolumeManager('btrfs', provider, 'root_dir', volumes)
        mock_btrfs.assert_called_once_with(
            provider, 'root_dir', volumes, None
        )
