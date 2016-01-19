from nose.tools import *
from mock import patch

import mock

import nose_helper
from collections import namedtuple

from kiwi.exceptions import *
from kiwi.volume_manager_btrfs import VolumeManagerBtrfs


class TestVolumeManagerBtrfs(object):
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
        self.volumes = [
            self.volume_type(
                name='LVRoot', size='freespace:100', realpath='/',
                mountpoint=None, fullsize=False
            ),
            self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False
            ),
            self.volume_type(
                name='myvol', size='size:500', realpath='/data',
                mountpoint='LVdata', fullsize=False
            ),
            self.volume_type(
                name='LVhome', size=None, realpath='/home',
                mountpoint='/home', fullsize=True
            ),
        ]
        mock_path.return_value = True
        self.device_provider = mock.Mock()
        self.device_provider.is_loop = mock.Mock(
            return_value=True
        )
        self.device_provider.get_device = mock.Mock(
            return_value='/dev/storage'
        )
        self.volume_manager = VolumeManagerBtrfs(
            self.device_provider, 'root_dir', self.volumes
        )

    def test_post_init(self):
        self.volume_manager.post_init({'some-arg': 'some-val'})
        assert self.volume_manager.custom_args['some-arg'] == 'some-val'

    def test_get_device(self):
        assert self.volume_manager.get_device() == \
            self.volume_manager.device_provider.get_device()

    @patch('os.path.exists')
    @patch('kiwi.volume_manager_btrfs.Command.run')
    @patch('kiwi.volume_manager_btrfs.FileSystem')
    @patch('kiwi.volume_manager_btrfs.MappedDevice')
    @patch('kiwi.volume_manager_base.mkdtemp')
    def test_setup(
        self, mock_temp, mock_mapped_device, mock_fs,
        mock_command, mock_os_exists
    ):
        mock_temp.return_value = 'tmpdir'
        command_call = mock.Mock()
        command_call.output = 'ID 4711 xx'
        mock_mapped_device.return_value = 'mapped_device'
        mock_os_exists.return_value = False
        mock_command.return_value = command_call

        self.volume_manager.setup()

        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'mount', '/dev/storage', 'tmpdir'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'btrfs', 'subvolume', 'create', 'tmpdir/@'
            ])
        call = mock_command.call_args_list[2]
        assert mock_command.call_args_list[2] == \
            call([
                'btrfs', 'subvolume', 'list', 'tmpdir'
            ])
        call = mock_command.call_args_list[3]
        assert mock_command.call_args_list[3] == \
            call([
                'btrfs', 'subvolume', 'set-default', '4711', 'tmpdir'
            ])

    @raises(KiwiVolumeRootIDError)
    @patch('os.path.exists')
    @patch('kiwi.volume_manager_btrfs.Command.run')
    @patch('kiwi.volume_manager_btrfs.FileSystem')
    @patch('kiwi.volume_manager_btrfs.MappedDevice')
    @patch('kiwi.volume_manager_base.mkdtemp')
    def test_setup_volume_id_not_detected(
        self, mock_temp, mock_mapped_device, mock_fs,
        mock_command, mock_os_exists
    ):
        command_call = mock.Mock()
        command_call.output = 'id-string-invalid'
        mock_mapped_device.return_value = 'mapped_device'
        mock_os_exists.return_value = False
        mock_command.return_value = command_call
        self.volume_manager.setup()

    @patch('os.path.exists')
    @patch('kiwi.volume_manager_btrfs.Command.run')
    def test_create_volumes(self, mock_command, mock_os_exists):
        self.volume_manager.mountpoint = 'tmpdir'
        mock_os_exists.return_value = False
        self.volume_manager.create_volumes('btrfs')

        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'mkdir', '-p', 'root_dir/etc'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'mkdir', '-p', 'root_dir/data'
            ])
        call = mock_command.call_args_list[2]
        assert mock_command.call_args_list[2] == \
            call([
                'mkdir', '-p', 'root_dir/home'
            ])
        call = mock_command.call_args_list[3]
        assert mock_command.call_args_list[3] == \
            call([
                'btrfs', 'subvolume', 'create', 'tmpdir/@/data/'
            ])
        call = mock_command.call_args_list[4]
        assert mock_command.call_args_list[4] == \
            call([
                'btrfs', 'subvolume', 'create', 'tmpdir/@/etc/'
            ])
        call = mock_command.call_args_list[5]
        assert mock_command.call_args_list[5] == \
            call([
                'btrfs', 'subvolume', 'create', 'tmpdir/@/home/'
            ])

    def test_mount_volumes(self):
        self.volume_manager.mount_volumes()

    @patch('kiwi.volume_manager_btrfs.DataSync')
    @patch('kiwi.volume_manager_btrfs.VolumeManagerBtrfs.is_mounted')
    def test_sync_data(self, mock_mounted, mock_sync):
        mock_mounted.return_value = True
        self.volume_manager.mountpoint = 'tmpdir'
        sync = mock.Mock()
        mock_sync.return_value = sync
        self.volume_manager.sync_data(['exclude_me'])
        mock_sync.assert_called_once_with('root_dir', 'tmpdir/@')
        sync.sync_data.assert_called_once_with(['exclude_me'])

    @patch('time.sleep')
    @patch('kiwi.volume_manager_btrfs.VolumeManagerBtrfs.is_mounted')
    @patch('kiwi.volume_manager_btrfs.Path.wipe')
    @patch('kiwi.volume_manager_btrfs.Command.run')
    def test_destructor_success(
        self, mock_command, mock_wipe, mock_mounted, mock_time
    ):
        self.volume_manager.mountpoint = 'tmpdir'
        mock_mounted.return_value = True
        self.volume_manager.__del__()
        mock_command.assert_called_once_with(['umount', '/dev/storage'])
        mock_wipe.assert_called_once_with('tmpdir')
        self.volume_manager.mountpoint = None

    @patch('time.sleep')
    @patch('kiwi.volume_manager_btrfs.VolumeManagerBtrfs.is_mounted')
    @patch('kiwi.volume_manager_btrfs.Path')
    @patch('kiwi.volume_manager_btrfs.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_destructor_failed(
        self, mock_log_warn, mock_command, mock_path, mock_mounted, mock_time
    ):
        self.volume_manager.mountpoint = 'tmpdir'
        mock_command.side_effect = Exception
        mock_mounted.return_value = True
        self.volume_manager.__del__()
        assert mock_log_warn.called
        self.volume_manager.mountpoint = None
