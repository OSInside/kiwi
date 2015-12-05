from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.volume_manager import VolumeManager


class TestVolumeManager(object):
    @raises(KiwiVolumeManagerSetupError)
    def test_volume_manager_not_implemented(self):
        VolumeManager.new('foo', mock.Mock(), 'source_dir', mock.Mock())

    @patch('kiwi.volume_manager.VolumeManagerLVM')
    @patch('os.path.exists')
    def test_volume_manager_lvm(self, mock_path, mock_lvm):
        mock_path.return_value = True
        provider = mock.Mock()
        volumes = mock.Mock()
        VolumeManager.new('lvm', provider, 'source_dir', volumes)
        mock_lvm.assert_called_once_with(
            provider, 'source_dir', volumes, None
        )

    @patch('kiwi.volume_manager.VolumeManagerBtrfs')
    @patch('os.path.exists')
    def test_volume_manager_btrfs(self, mock_path, mock_btrfs):
        mock_path.return_value = True
        provider = mock.Mock()
        volumes = mock.Mock()
        VolumeManager.new('btrfs', provider, 'source_dir', volumes)
        mock_btrfs.assert_called_once_with(
            provider, 'source_dir', volumes, None
        )
