from nose.tools import *
from mock import patch

import mock

import nose_helper
from collections import namedtuple

from kiwi.exceptions import *
from kiwi.volume_manager_lvm import VolumeManagerLVM
from kiwi.defaults import Defaults


class TestVolumeManagerLVM(object):
    @patch('os.path.exists')
    def setup(self, mock_path):
        self.mount_type = namedtuple(
            'mount_type', [
                'device', 'mountpoint'
            ]
        )
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
        self.volume_manager = VolumeManagerLVM(
            self.device_provider, 'source_dir', self.volumes
        )

    def test_post_init(self):
        self.volume_manager.post_init({'some-arg': 'some-val'})
        assert self.volume_manager.custom_args['some-arg'] == 'some-val'

    @patch('os.path.exists')
    def test_get_device(self, mock_path):
        mock_path.return_value = True
        self.volume_manager.volume_map = {
            'LVRoot': '/dev/lvroot', 'LVx': '/dev/lvx'
        }
        assert self.volume_manager.get_device()['LVx'].get_device() == \
            '/dev/lvx'
        assert self.volume_manager.get_device()['root'].get_device() == \
            '/dev/lvroot'

    @patch('kiwi.volume_manager_lvm.Command.run')
    def test_setup(self, mock_command):
        self.volume_manager.setup('volume_group')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'vgs', '--noheadings', '-o', 'vg_name'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call(
                command=['vgremove', '--force', 'volume_group'],
                raise_on_error=False)
        call = mock_command.call_args_list[2]
        assert mock_command.call_args_list[2] == \
            call([
                'pvcreate', '/dev/storage'
            ])
        call = mock_command.call_args_list[3]
        assert mock_command.call_args_list[3] == \
            call([
                'vgcreate', 'volume_group', '/dev/storage'
            ])
        assert self.volume_manager.volume_group == 'volume_group'
        self.volume_manager.volume_group = None

    @raises(KiwiVolumeGroupConflict)
    @patch('kiwi.volume_manager_lvm.Command.run')
    def test_setup_volume_group_host_conflict(self, mock_command):
        command = mock.Mock()
        command.output = 'volume_group'
        mock_command.return_value = command
        self.volume_manager.setup('volume_group')

    @patch('os.path.exists')
    @patch('kiwi.volume_manager_base.SystemSize')
    @patch('kiwi.volume_manager_lvm.Command.run')
    @patch('kiwi.volume_manager_lvm.FileSystem.new')
    @patch('kiwi.volume_manager_lvm.MappedDevice')
    def test_create_volumes(
        self, mock_mapped_device, mock_fs, mock_command, mock_size,
        mock_os_exists
    ):
        mock_mapped_device.return_value = 'mapped_device'
        size = mock.Mock()
        size.customize = mock.Mock(
            return_value=42
        )
        mock_size.return_value = size
        mock_os_exists.return_value = False
        self.volume_manager.volume_group = 'volume_group'
        self.volume_manager.create_volumes('ext3')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'mkdir', '-p', 'source_dir//etc'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'mkdir', '-p', 'source_dir//data'
            ])
        call = mock_command.call_args_list[2]
        assert mock_command.call_args_list[2] == \
            call([
                'mkdir', '-p', 'source_dir//home'
            ])
        size = 500
        call = mock_command.call_args_list[3]
        assert mock_command.call_args_list[3] == \
            call([
                'lvcreate', '-L', format(size), '-n', 'myvol', 'volume_group'
            ])
        size = 200 + 42 + Defaults.get_min_volume_mbytes()
        call = mock_command.call_args_list[4]
        assert mock_command.call_args_list[4] == \
            call([
                'lvcreate', '-L', format(size), '-n', 'LVetc', 'volume_group'
            ])
        size = 100 + 42 + Defaults.get_min_volume_mbytes()
        call = mock_command.call_args_list[5]
        assert mock_command.call_args_list[5] == \
            call([
                'lvcreate', '-L', format(size), '-n', 'LVRoot', 'volume_group'
            ])
        call = mock_command.call_args_list[6]
        assert mock_command.call_args_list[6] == \
            call([
                'lvcreate', '-l', '+100%FREE', '-n', 'LVhome', 'volume_group'
            ])
        call = mock_fs.call_args_list[0]
        assert mock_fs.call_args_list[0] == \
            call('ext3', 'mapped_device')
        call = mock_fs.call_args_list[1]
        assert mock_fs.call_args_list[1] == \
            call('ext3', 'mapped_device')
        call = mock_fs.call_args_list[2]
        assert mock_fs.call_args_list[2] == \
            call('ext3', 'mapped_device')
        call = mock_fs.call_args_list[3]
        assert mock_fs.call_args_list[3] == \
            call('ext3', 'mapped_device')
        assert self.volume_manager.mount_list == [
            self.mount_type(
                device='/dev/volume_group/LVRoot', mountpoint='/'
            ),
            self.mount_type(
                device='/dev/volume_group/myvol', mountpoint='//data'
            ),
            self.mount_type(
                device='/dev/volume_group/LVetc', mountpoint='//etc'
            ),
            self.mount_type(
                device='/dev/volume_group/LVhome', mountpoint='//home'
            )
        ]
        self.volume_manager.volume_group = None

    @patch('kiwi.volume_manager_lvm.Path')
    @patch('kiwi.volume_manager_base.mkdtemp')
    @patch('kiwi.volume_manager_lvm.Command.run')
    def test_mount_volumes(self, mock_command, mock_temp, mock_path):
        mock_temp.return_value = 'tmpdir'
        self.volume_manager.mount_list = [
            self.mount_type(device='/dev/volume_group/LVRoot', mountpoint='/')
        ]
        self.volume_manager.mount_volumes()
        mock_path.create.assert_called_once_with('tmpdir/')
        mock_command.assert_called_once_with(
            ['mount', '/dev/volume_group/LVRoot', 'tmpdir/']
        )

    @patch('time.sleep')
    @patch('kiwi.volume_manager_lvm.VolumeManagerLVM.is_mounted')
    @patch('kiwi.volume_manager_lvm.Path.wipe')
    @patch('kiwi.volume_manager_lvm.Command.run')
    def test_destructor_success(
        self, mock_command, mock_wipe, mock_mounted, mock_time
    ):
        self.volume_manager.mountpoint = 'tmpdir'
        self.volume_manager.mount_list = [
            self.mount_type(device='/dev/volume_group/LVRoot', mountpoint='/')
        ]
        mock_mounted.return_value = True
        self.volume_manager.volume_group = 'volume_group'
        self.volume_manager.__del__()
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call([
                'umount', '/dev/volume_group/LVRoot'
            ])
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == \
            call([
                'vgchange', '-an', 'volume_group'
            ])
        mock_wipe.assert_called_once_with('tmpdir')
        self.volume_manager.volume_group = None

    @patch('time.sleep')
    @patch('kiwi.volume_manager_lvm.VolumeManagerLVM.is_mounted')
    @patch('kiwi.volume_manager_lvm.Path')
    @patch('kiwi.volume_manager_lvm.Command.run')
    @patch('kiwi.logger.log.warning')
    def test_destructor_failed(
        self, mock_log_warn, mock_command, mock_path, mock_mounted, mock_time
    ):
        self.volume_manager.mountpoint = 'tmpdir'
        mock_command.side_effect = Exception
        self.volume_manager.mount_list = [
            self.mount_type(device='/dev/volume_group/LVRoot', mountpoint='/')
        ]
        mock_mounted.return_value = True
        self.volume_manager.volume_group = 'volume_group'
        self.volume_manager.__del__()
        assert mock_log_warn.called
        self.volume_manager.volume_group = None
