from mock import patch

import mock

from .test_helper import raises

from kiwi.exceptions import KiwiVolumeManagerSetupError

from kiwi.volume_manager import VolumeManager


class TestVolumeManager(object):
    @raises(KiwiVolumeManagerSetupError)
    def test_volume_manager_not_implemented(self):
        VolumeManager('foo', mock.Mock(), 'root_dir', mock.Mock())

    @patch('kiwi.volume_manager.VolumeManagerLVM')
    @patch('os.path.exists')
    def test_volume_manager_lvm(self, mock_path, mock_lvm):
        mock_path.return_value = True
        provider = mock.Mock()
        volumes = mock.Mock()
        VolumeManager('lvm', provider, 'root_dir', volumes)
        mock_lvm.assert_called_once_with(
            provider, 'root_dir', volumes, None
        )

    @patch('kiwi.volume_manager.VolumeManagerBtrfs')
    @patch('os.path.exists')
    def test_volume_manager_btrfs(self, mock_path, mock_btrfs):
        mock_path.return_value = True
        provider = mock.Mock()
        volumes = mock.Mock()
        VolumeManager('btrfs', provider, 'root_dir', volumes)
        mock_btrfs.assert_called_once_with(
            provider, 'root_dir', volumes, None
        )
