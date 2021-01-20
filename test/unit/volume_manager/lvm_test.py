import logging
from mock import (
    patch, call, Mock
)
from pytest import (
    raises, fixture
)
from collections import namedtuple

from kiwi.volume_manager.lvm import VolumeManagerLVM
from kiwi.defaults import Defaults

from kiwi.exceptions import KiwiVolumeGroupConflict


class TestVolumeManagerLVM:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    def setup(self, mock_path):
        self.volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize',
                'label',
                'attributes',
                'is_root_volume'
            ]
        )
        self.volumes = [
            self.volume_type(
                name='LVRoot', size='freespace:100', realpath='/',
                mountpoint=None, fullsize=False, label=None, attributes=[],
                is_root_volume=True
            ),
            self.volume_type(
                name='LVSwap', size='size:100', realpath='swap',
                mountpoint=None, fullsize=False, label='SWAP', attributes=[],
                is_root_volume=False
            ),
            self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False, label='etc', attributes=[],
                is_root_volume=False
            ),
            self.volume_type(
                name='myvol', size='size:500', realpath='/data',
                mountpoint='LVdata', fullsize=False, label=None, attributes=[],
                is_root_volume=False
            ),
            self.volume_type(
                name='LVhome', size=None, realpath='/home',
                mountpoint='/home', fullsize=True, label=None, attributes=[],
                is_root_volume=False
            ),
        ]
        mock_path.return_value = True
        self.device_map = {
            'root': Mock()
        }
        self.device_map['root'].is_loop = Mock(
            return_value=True
        )
        self.device_map['root'].get_device = Mock(
            return_value='/dev/storage'
        )
        self.volume_manager = VolumeManagerLVM(
            self.device_map, 'root_dir', self.volumes,
            {'some-arg': 'some-val', 'fs_mount_options': ['a,b,c']}
        )
        assert self.volume_manager.mount_options == 'a,b,c'

    def test_post_init_custom_args(self):
        self.volume_manager.post_init({'some-arg': 'some-val'})
        assert self.volume_manager.custom_args['some-arg'] == 'some-val'

    def test_post_init_no_additional_custom_args(self):
        self.volume_manager.post_init(None)
        assert self.volume_manager.custom_args == {
            'root_label': 'ROOT', 'resize_on_boot': False
        }

    def test_post_init_no_mount_options(self):
        self.volume_manager.custom_filesystem_args['mount_options'] = None
        self.volume_manager.post_init(None)
        assert self.volume_manager.mount_options == 'defaults'

    @patch('os.path.exists')
    def test_get_device(self, mock_path):
        mock_path.return_value = True
        self.volume_manager.volume_map = {
            'LVRoot': '/dev/lvroot', 'LVx': '/dev/lvx',
            'LVSwap': '/dev/lvswap', 'LVs': '/dev/lvs'
        }
        assert self.volume_manager.get_device()['LVx'].get_device() == \
            '/dev/lvx'
        assert self.volume_manager.get_device()['root'].get_device() == \
            '/dev/lvroot'
        assert self.volume_manager.get_device()['swap'].get_device() == \
            '/dev/lvswap'

    @patch('kiwi.volume_manager.lvm.Command.run')
    @patch('kiwi.volume_manager.base.mkdtemp')
    def test_setup(self, mock_mkdtemp, mock_command):
        mock_mkdtemp.return_value = 'tmpdir'
        command = Mock()
        # no output for commands to mock empty information for
        # vgs command, indicating the volume group is not in use
        command.output = ''
        mock_command.return_value = command
        self.volume_manager.setup('volume_group')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == call(
            ['vgs', '--noheadings', '--select', 'vg_name=volume_group']
        )
        call = mock_command.call_args_list[1]
        assert mock_command.call_args_list[1] == call(
            command=['vgremove'] + self.volume_manager.lvm_tool_options + [
                '--force', 'volume_group'
            ], raise_on_error=False
        )
        call = mock_command.call_args_list[2]
        assert mock_command.call_args_list[2] == call(
            ['pvcreate'] + self.volume_manager.lvm_tool_options + [
                '/dev/storage'
            ]
        )
        call = mock_command.call_args_list[3]
        assert mock_command.call_args_list[3] == call(
            ['vgcreate'] + self.volume_manager.lvm_tool_options + [
                'volume_group', '/dev/storage'
            ]
        )
        assert self.volume_manager.volume_group == 'volume_group'
        self.volume_manager.volume_group = None

    @patch('kiwi.volume_manager.lvm.Command.run')
    @patch('kiwi.volume_manager.base.mkdtemp')
    def test_setup_volume_group_host_conflict(self, mock_mkdtemp, mock_command):
        command = Mock()
        command.output = 'some_data_about_volume_group'
        mock_command.return_value = command
        with raises(KiwiVolumeGroupConflict):
            self.volume_manager.setup('volume_group')

    @patch('os.path.exists')
    @patch('kiwi.path.Path.create')
    @patch('kiwi.volume_manager.base.SystemSize')
    @patch('kiwi.volume_manager.lvm.Command.run')
    @patch('kiwi.volume_manager.lvm.FileSystem.new')
    @patch('kiwi.volume_manager.lvm.MappedDevice')
    @patch('kiwi.volume_manager.lvm.MountManager')
    @patch('kiwi.volume_manager.base.VolumeManagerBase.apply_attributes_on_volume')
    def test_create_volumes(
        self, mock_attrs, mock_mount, mock_mapped_device, mock_fs,
        mock_command, mock_size, mock_create, mock_os_exists
    ):
        mock_os_exists_return_list = [True, True, False, False, False]

        def mock_os_exists_return(path):
            return mock_os_exists_return_list.pop()

        mock_os_exists.side_effect = mock_os_exists_return
        filesystem = Mock()
        mock_fs.return_value = filesystem
        self.volume_manager.mountpoint = 'tmpdir'
        mock_mapped_device.return_value = 'mapped_device'
        size = Mock()
        size.customize = Mock(
            return_value=42
        )
        mock_size.return_value = size
        self.volume_manager.volume_group = 'volume_group'
        self.volume_manager.create_volumes('ext3')
        myvol_size = 500
        etc_size = 200 + 42 + Defaults.get_min_volume_mbytes()
        root_size = 100 + 42 + Defaults.get_min_volume_mbytes()

        assert mock_attrs.call_args_list == [
            call(
                'root_dir', self.volume_type(
                    name='LVSwap', size='size:100', realpath='swap',
                    mountpoint=None, fullsize=False, label='SWAP',
                    attributes=[], is_root_volume=False
                )
            ),
            call(
                'root_dir', self.volume_type(
                    name='LVRoot', size='freespace:100', realpath='/',
                    mountpoint=None, fullsize=False, label=None,
                    attributes=[], is_root_volume=True
                )
            ),
            call(
                'root_dir', self.volume_type(
                    name='myvol', size='size:500', realpath='/data',
                    mountpoint='LVdata', fullsize=False, label=None,
                    attributes=[], is_root_volume=False
                )
            ),
            call(
                'root_dir', self.volume_type(
                    name='LVetc', size='freespace:200', realpath='/etc',
                    mountpoint='/etc', fullsize=False, label='etc',
                    attributes=[], is_root_volume=False
                )
            )
        ]
        assert mock_mount.call_args_list == [
            call(device='/dev/volume_group/LVRoot', mountpoint='tmpdir'),
            call(device='/dev/volume_group/myvol', mountpoint='tmpdir//data'),
            call(device='/dev/volume_group/LVetc', mountpoint='tmpdir//etc'),
            call(device='/dev/volume_group/LVhome', mountpoint='tmpdir//home')
        ]
        assert mock_command.call_args_list == [
            call(
                ['lvcreate'] + self.volume_manager.lvm_tool_options + [
                    '-Zn', '-L', '100', '-n', 'LVSwap', 'volume_group'
                ]
            ),
            call(
                ['vgscan'] + self.volume_manager.lvm_tool_options + [
                    '--mknodes'
                ]
            ),
            call(
                ['lvcreate'] + self.volume_manager.lvm_tool_options + [
                    '-Zn', '-L', format(root_size), '-n', 'LVRoot',
                    'volume_group'
                ]
            ),
            call(
                ['vgscan'] + self.volume_manager.lvm_tool_options + [
                    '--mknodes'
                ]
            ),
            call(
                ['lvcreate'] + self.volume_manager.lvm_tool_options + [
                    '-Zn', '-L', format(myvol_size), '-n', 'myvol',
                    'volume_group'
                ]
            ),
            call(
                ['vgscan'] + self.volume_manager.lvm_tool_options + [
                    '--mknodes'
                ]
            ),
            call(
                ['lvcreate'] + self.volume_manager.lvm_tool_options + [
                    '-Zn', '-L', format(etc_size), '-n', 'LVetc',
                    'volume_group'
                ]
            ),
            call(
                ['vgscan'] + self.volume_manager.lvm_tool_options + [
                    '--mknodes'
                ]
            ),
            call(
                ['lvcreate'] + self.volume_manager.lvm_tool_options + [
                    '-Zn', '-l', '+100%FREE', '-n', 'LVhome', 'volume_group'
                ]
            ),
            call(
                ['vgscan'] + self.volume_manager.lvm_tool_options + [
                    '--mknodes'
                ]
            )
        ]
        assert mock_fs.call_args_list == [
            call(
                custom_args={'create_options': [], 'mount_options': ['a,b,c']},
                device_provider='mapped_device',
                name='ext3'
            ),
            call(
                custom_args={'create_options': [], 'mount_options': ['a,b,c']},
                device_provider='mapped_device',
                name='ext3'
            ),
            call(
                custom_args={'create_options': [], 'mount_options': ['a,b,c']},
                device_provider='mapped_device',
                name='ext3'
            ),
            call(
                custom_args={'create_options': [], 'mount_options': ['a,b,c']},
                device_provider='mapped_device',
                name='ext3'
            )
        ]
        assert filesystem.create_on_device.call_args_list == [
            call(label='ROOT'),
            call(label=None),
            call(label='etc'),
            call(label=None)
        ]

        assert mock_create.call_args_list == [
            call('root_dir/etc'), call('root_dir/data'), call('root_dir/home')
        ]
        self.volume_manager.volume_group = None

    @patch('kiwi.volume_manager.lvm.Path')
    def test_mount_volumes(self, mock_path):
        volume_mount = Mock()
        volume_mount.mountpoint = 'volume_mount_point'
        self.volume_manager.mount_list = [volume_mount]
        self.volume_manager.mount_volumes()
        mock_path.create.assert_called_once_with(volume_mount.mountpoint)
        volume_mount.mount.assert_called_once_with(options=['a,b,c'])

    def test_umount_volumes(self):
        volume_mount = Mock()
        volume_mount.mountpoint = 'volume_mount_point'
        self.volume_manager.mount_list = [volume_mount]
        assert self.volume_manager.umount_volumes() is True
        volume_mount.umount.assert_called_once_with()

    def test_get_volumes(self):
        volume_mount = Mock()
        volume_mount.mountpoint = \
            '/tmp/kiwi_volumes.f2qx_d3y/boot/grub2/x86_64-efi'
        volume_mount.device = '/dev/mapper/vg1-LVRoot'
        self.volume_manager.mount_list = [volume_mount]
        assert self.volume_manager.get_volumes() == {
            'boot/grub2/x86_64-efi': {
                'volume_options': 'a,b,c',
                'volume_device': '/dev/mapper/vg1-LVRoot'
            }
        }

    def test_get_fstab(self):
        volume_mount = Mock()
        volume_mount.mountpoint = '/tmp/kiwi_volumes.f2qx_d3y/var/tmp'
        volume_mount.device = 'device'
        self.volume_manager.mount_list = [volume_mount]
        assert self.volume_manager.get_fstab(None, 'ext3') == [
            'device /var/tmp ext3 a,b,c 1 2'
        ]

    @patch('kiwi.volume_manager.lvm.Path.wipe')
    @patch('kiwi.volume_manager.lvm.Command.run')
    def test_destructor_busy_volumes(self, mock_command, mock_wipe):
        self.volume_manager.mountpoint = 'tmpdir'
        self.volume_manager.volume_group = 'volume_group'
        volume_mount = Mock()
        volume_mount.is_mounted.return_value = True
        volume_mount.umount.return_value = False
        volume_mount.mountpoint = 'volume_mount_point'
        volume_mount.device = '/dev/volume_group/LVRoot'
        self.volume_manager.mount_list = [volume_mount]

        self.volume_manager.__del__()

        volume_mount.umount.assert_called_once_with()
        self.volume_manager.volume_group = None

    @patch('kiwi.volume_manager.lvm.VolumeManagerLVM.umount_volumes')
    @patch('kiwi.volume_manager.lvm.Path.wipe')
    @patch('kiwi.volume_manager.lvm.Command.run')
    def test_destructor(
        self, mock_command, mock_wipe, mock_umount_volumes
    ):
        mock_umount_volumes.return_value = True
        mock_command.side_effect = Exception
        self.volume_manager.mountpoint = 'tmpdir'
        self.volume_manager.volume_group = 'volume_group'

        with self._caplog.at_level(logging.WARNING):
            self.volume_manager.__del__()
            mock_umount_volumes.assert_called_once_with()
            mock_wipe.assert_called_once_with('tmpdir')
            mock_command.assert_called_once_with(
                ['vgchange'] + self.volume_manager.lvm_tool_options + [
                    '-an', 'volume_group'
                ]
            )
            self.volume_manager.volume_group = None
