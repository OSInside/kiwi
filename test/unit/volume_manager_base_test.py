from nose.tools import *
from mock import patch

import mock

import nose_helper

from collections import namedtuple
from kiwi.exceptions import *
from kiwi.volume_manager_base import VolumeManagerBase


class TestVolumeManagerBase(object):
    @patch('os.path.exists')
    def setup(self, mock_path):
        self.volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize'
            ]
        )
        mock_path.return_value = True
        self.device_provider = mock.Mock()
        self.device_provider.is_loop = mock.Mock(
            return_value=True
        )
        self.device_provider.get_device = mock.Mock(
            return_value='/dev/storage'
        )
        self.volume_manager = VolumeManagerBase(
            self.device_provider, 'source_dir', mock.Mock()
        )

    @raises(KiwiVolumeManagerSetupError)
    def test_source_dir_does_not_exist(self):
        VolumeManagerBase(mock.Mock(), 'source_dir', mock.Mock())

    def test_is_loop(self):
        assert self.volume_manager.is_loop() == \
            self.device_provider.is_loop()

    def test_get_device(self):
        assert self.volume_manager.get_device() == \
            self.device_provider.get_device()

    @raises(NotImplementedError)
    def test_setup(self):
        self.volume_manager.setup()

    @raises(NotImplementedError)
    def test_create_volumes(self):
        self.volume_manager.create_volumes('ext3')

    @patch('kiwi.volume_manager_base.Path.create')
    @patch('os.path.exists')
    def test_create_volume_paths_in_source_dir(self, mock_os_path, mock_path):
        mock_os_path.return_value = False
        self.volume_manager.volumes = [
            self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False
            )
        ]
        self.volume_manager.create_volume_paths_in_source_dir()
        mock_path.assert_called_once_with('source_dir//etc')

    def test_get_canonical_volume_list(self):
        self.volume_manager.volumes = [
            self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False
            ),
            self.volume_type(
                name='LVRoot', size='size:500', realpath='/',
                mountpoint='/', fullsize=True
            )
        ]
        volume_list = self.volume_manager.get_canonical_volume_list()
        assert volume_list.volumes[0].name == 'LVetc'
        assert volume_list.full_size_volume.name == 'LVRoot'

    @patch('kiwi.volume_manager_base.SystemSize')
    def test_get_volume_mbsize(self, mock_size):
        size = mock.Mock()
        size.customize = mock.Mock(
            return_value=42
        )
        mock_size.return_value = size
        assert self.volume_manager.get_volume_mbsize(
            100, 'freespace', '/foo', 'ext3'
        ) == 172

    @raises(NotImplementedError)
    def test_mount_volumes(self):
        self.volume_manager.mount_volumes()

    @patch('kiwi.volume_manager_base.Command.run')
    def test_is_mounted_true(self, mock_command):
        self.volume_manager.mountpoint = 'mountpoint'
        assert self.volume_manager.is_mounted() == True
        mock_command.assert_called_once_with(
            ['mountpoint', 'mountpoint']
        )

    @patch('kiwi.volume_manager_base.Command.run')
    def test_is_mounted_false(self, mock_command):
        mock_command.side_effect = Exception
        self.volume_manager.mountpoint = 'mountpoint'
        assert self.volume_manager.is_mounted() == False
        mock_command.assert_called_once_with(
            ['mountpoint', 'mountpoint']
        )

    @patch('kiwi.volume_manager_base.DataSync')
    @patch('kiwi.volume_manager_base.VolumeManagerBase.is_mounted')
    def test_sync_data(self, mock_mounted, mock_sync):
        data_sync = mock.Mock()
        mock_sync.return_value = data_sync
        mock_mounted.return_value = True
        self.volume_manager.mountpoint = 'mountpoint'
        self.volume_manager.sync_data(['exclude_me'])
        mock_sync.assert_called_once_with(
            'source_dir', 'mountpoint'
        )
        data_sync.sync_data.assert_called_once_with(['exclude_me'])

    @patch('kiwi.volume_manager_base.mkdtemp')
    def test_setup_mountpoint(self, mock_mkdtemp):
        mock_mkdtemp.return_value = 'tmpdir'
        self.volume_manager.setup_mountpoint()
        assert self.volume_manager.mountpoint == 'tmpdir'

    def test_destructor(self):
        # does nothing by default, just pass
        self.volume_manager.__del__()
