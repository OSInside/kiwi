from mock import patch
from mock import call
import mock

import datetime

from .test_helper import raises, patch_open
from lxml import etree
from xml.dom import minidom
from collections import namedtuple

from kiwi.exceptions import (
    KiwiVolumeRootIDError,
    KiwiVolumeManagerSetupError
)
from kiwi.volume_manager.btrfs import VolumeManagerBtrfs


class TestVolumeManagerBtrfs(object):
    @patch('os.path.exists')
    def setup(self, mock_path):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)
        self.volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize',
                'attributes'
            ]
        )
        self.volumes = [
            self.volume_type(
                name='LVRoot', size='freespace:100', realpath='/',
                mountpoint=None, fullsize=False,
                attributes=[]
            ),
            self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False,
                attributes=[]
            ),
            self.volume_type(
                name='myvol', size='size:500', realpath='/data',
                mountpoint='LVdata', fullsize=False,
                attributes=[]
            ),
            self.volume_type(
                name='LVhome', size=None, realpath='/home',
                mountpoint='/home', fullsize=True,
                attributes=[]
            )
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

    @patch('os.path.exists')
    @patch('kiwi.volume_manager.btrfs.Command.run')
    @patch('kiwi.volume_manager.btrfs.FileSystem')
    @patch('kiwi.volume_manager.btrfs.MappedDevice')
    @patch('kiwi.volume_manager.btrfs.MountManager')
    @patch('kiwi.volume_manager.base.mkdtemp')
    def test_setup_no_snapshot(
        self, mock_mkdtemp, mock_mount, mock_mapped_device, mock_fs,
        mock_command, mock_os_exists
    ):
        mock_mkdtemp.return_value = 'tmpdir'
        toplevel_mount = mock.Mock()
        mock_mount.return_value = toplevel_mount
        command_call = mock.Mock()
        command_call.output = 'ID 256 gen 23 top level 5 path @'
        mock_mapped_device.return_value = 'mapped_device'
        mock_os_exists.return_value = False
        mock_command.return_value = command_call

        self.volume_manager.setup()

        mock_mount.assert_called_once_with(
            device='/dev/storage', mountpoint='tmpdir'
        )
        toplevel_mount.mount.assert_called_once_with([])
        assert mock_command.call_args_list == [
            call(['btrfs', 'subvolume', 'create', 'tmpdir/@']),
            call(['btrfs', 'subvolume', 'list', 'tmpdir']),
            call(['btrfs', 'subvolume', 'set-default', '256', 'tmpdir'])
        ]

    @patch('os.path.exists')
    @patch('kiwi.volume_manager.btrfs.Command.run')
    @patch('kiwi.volume_manager.btrfs.FileSystem')
    @patch('kiwi.volume_manager.btrfs.MappedDevice')
    @patch('kiwi.volume_manager.btrfs.MountManager')
    @patch('kiwi.volume_manager.base.mkdtemp')
    def test_setup_with_snapshot(
        self, mock_mkdtemp, mock_mount, mock_mapped_device, mock_fs,
        mock_command, mock_os_exists
    ):
        mock_mkdtemp.return_value = 'tmpdir'
        toplevel_mount = mock.Mock()
        mock_mount.return_value = toplevel_mount
        command_call = mock.Mock()
        command_call.output = \
            'ID 258 gen 26 top level 257 path @/.snapshots/1/snapshot'
        mock_mapped_device.return_value = 'mapped_device'
        mock_os_exists.return_value = False
        mock_command.return_value = command_call
        self.volume_manager.custom_args['root_is_snapshot'] = True
        self.volume_manager.custom_args['quota_groups'] = True

        self.volume_manager.setup()

        mock_mount.assert_called_once_with(
            device='/dev/storage', mountpoint='tmpdir'
        )
        toplevel_mount.mount.assert_called_once_with([])
        assert mock_command.call_args_list == [
            call(['btrfs', 'quota', 'enable', 'tmpdir']),
            call(['btrfs', 'subvolume', 'create', 'tmpdir/@']),
            call(['btrfs', 'subvolume', 'create', 'tmpdir/@/.snapshots']),
            call(['mkdir', '-p', 'tmpdir/@/.snapshots/1']),
            call([
                'btrfs', 'subvolume', 'snapshot', 'tmpdir/@',
                'tmpdir/@/.snapshots/1/snapshot'
            ]),
            call(['btrfs', 'subvolume', 'list', 'tmpdir']),
            call(['btrfs', 'subvolume', 'set-default', '258', 'tmpdir'])
        ]

    @raises(KiwiVolumeRootIDError)
    @patch('os.path.exists')
    @patch('kiwi.volume_manager.btrfs.Command.run')
    @patch('kiwi.volume_manager.btrfs.FileSystem')
    @patch('kiwi.volume_manager.btrfs.MappedDevice')
    @patch('kiwi.volume_manager.btrfs.MountManager')
    def test_setup_volume_id_not_detected(
        self, mock_mount, mock_mapped_device, mock_fs,
        mock_command, mock_os_exists
    ):
        command_call = mock.Mock()
        command_call.output = 'id-string-invalid'
        mock_mapped_device.return_value = 'mapped_device'
        mock_os_exists.return_value = False
        mock_command.return_value = command_call
        self.volume_manager.setup()

    @patch('os.path.exists')
    @patch('kiwi.volume_manager.btrfs.Command.run')
    @patch('kiwi.volume_manager.btrfs.MountManager')
    @patch('kiwi.volume_manager.btrfs.Path.create')
    @patch('kiwi.volume_manager.base.VolumeManagerBase.apply_attributes_on_volume')
    def test_create_volumes(
        self, mock_attrs, mock_path, mock_mount, mock_command, mock_os_exists
    ):
        volume_mount = mock.Mock()
        mock_mount.return_value = volume_mount
        self.volume_manager.mountpoint = 'tmpdir'
        self.volume_manager.custom_args['root_is_snapshot'] = True
        mock_os_exists.return_value = False

        self.volume_manager.create_volumes('btrfs')

        assert mock_attrs.call_args_list == [
            call(
                'tmpdir/@/', self.volume_type(
                    name='myvol', size='size:500', realpath='/data',
                    mountpoint='LVdata', fullsize=False, attributes=[])
            ),
            call('tmpdir/@/', self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False, attributes=[])
            ),
            call('tmpdir/@/', self.volume_type(
                name='LVhome', size=None, realpath='/home',
                mountpoint='/home', fullsize=True, attributes=[])
            )
        ]
        assert mock_path.call_args_list == [
            call('root_dir/etc'),
            call('root_dir/data'),
            call('root_dir/home'),
            call('tmpdir/@'),
            call('tmpdir/@'),
            call('tmpdir/@')
        ]
        assert mock_command.call_args_list == [
            call(['btrfs', 'subvolume', 'create', 'tmpdir/@/data']),
            call(['btrfs', 'subvolume', 'create', 'tmpdir/@/etc']),
            call(['btrfs', 'subvolume', 'create', 'tmpdir/@/home'])
        ]
        assert mock_mount.call_args_list == [
            call(
                device='/dev/storage',
                mountpoint='tmpdir/@/.snapshots/1/snapshot/data'
            ),
            call(
                device='/dev/storage',
                mountpoint='tmpdir/@/.snapshots/1/snapshot/etc'
            ),
            call(
                device='/dev/storage',
                mountpoint='tmpdir/@/.snapshots/1/snapshot/home'
            )
        ]

    def test_get_volumes(self):
        volume_mount = mock.Mock()
        volume_mount.mountpoint = \
            '/tmp/kiwi_volumes.xx/@/.snapshots/1/snapshot/boot/grub2'
        volume_mount.device = 'device'
        self.volume_manager.toplevel_volume = '@/.snapshots/1/snapshot'
        self.volume_manager.subvol_mount_list = [volume_mount]
        self.volume_manager.custom_args['root_is_snapshot'] = True
        assert self.volume_manager.get_volumes() == {
            '/boot/grub2': {
                'volume_options': 'subvol=@/boot/grub2',
                'volume_device': 'device'
            }
        }

    @patch('kiwi.volume_manager.btrfs.Command.run')
    def test_get_fstab(self, mock_command):
        blkid_result = mock.Mock()
        blkid_result.output = 'id'
        mock_command.return_value = blkid_result
        volume_mount = mock.Mock()
        volume_mount.mountpoint = \
            '/tmp/kiwi_volumes.xx/@/.snapshots/1/snapshot/var/tmp'
        volume_mount.device = 'device'
        self.volume_manager.toplevel_volume = '@/.snapshots/1/snapshot'
        self.volume_manager.subvol_mount_list = [volume_mount]
        self.volume_manager.custom_args['root_is_snapshot'] = True
        assert self.volume_manager.get_fstab() == [
            'LABEL=id /.snapshots btrfs defaults,subvol=@/.snapshots 0 0',
            'LABEL=id /var/tmp btrfs defaults,subvol=@/var/tmp 0 0'
        ]

    @patch('os.path.exists')
    @patch('kiwi.volume_manager.btrfs.Path.create')
    def test_mount_volumes(self, mock_path, mock_os_exists):
        self.volume_manager.toplevel_mount = mock.Mock()
        self.volume_manager.toplevel_mount.is_mounted = mock.Mock(
            return_value=False
        )
        mock_os_exists.return_value = False
        volume_mount = mock.Mock()
        volume_mount.mountpoint = \
            '/tmp/kiwi_volumes.xx/@/.snapshots/1/snapshot/var/tmp'
        self.volume_manager.toplevel_volume = '@/.snapshots/1/snapshot'
        self.volume_manager.custom_args['root_is_snapshot'] = True
        self.volume_manager.subvol_mount_list = [volume_mount]

        self.volume_manager.mount_volumes()

        self.volume_manager.toplevel_mount.mount.assert_called_once_with([])
        mock_path.assert_called_once_with(volume_mount.mountpoint)
        volume_mount.mount.assert_called_once_with(
            options=['subvol=@/var/tmp']
        )

    @patch('os.path.exists')
    @patch('kiwi.volume_manager.btrfs.Command.run')
    @patch('kiwi.volume_manager.btrfs.FileSystem')
    @patch('kiwi.volume_manager.btrfs.MappedDevice')
    @patch('kiwi.volume_manager.btrfs.MountManager')
    @patch('kiwi.volume_manager.base.mkdtemp')
    def test_remount_volumes(
        self, mock_mkdtemp, mock_mount, mock_mapped_device, mock_fs,
        mock_command, mock_os_exists
    ):
        mock_mkdtemp.return_value = '/tmp/kiwi_volumes.xx'
        toplevel_mount = mock.Mock()
        toplevel_mount.is_mounted = mock.Mock(
            return_value=False
        )
        mock_mount.return_value = toplevel_mount
        command_call = mock.Mock()
        command_call.output = \
            'ID 258 gen 26 top level 257 path @/.snapshots/1/snapshot'
        mock_mapped_device.return_value = 'mapped_device'
        mock_os_exists.return_value = False
        mock_command.return_value = command_call
        self.volume_manager.custom_args['root_is_snapshot'] = True

        self.volume_manager.setup()

        mock_os_exists.return_value = True
        volume_mount = mock.Mock()
        volume_mount.mountpoint = \
            '/tmp/kiwi_volumes.xx/@/.snapshots/1/snapshot/var/tmp'
        self.volume_manager.subvol_mount_list = [volume_mount]

        self.volume_manager.mount_volumes()
        self.volume_manager.umount_volumes()
        self.volume_manager.mount_volumes()

        assert volume_mount.mountpoint == '/tmp/kiwi_volumes.xx/var/tmp'

    def test_umount_volumes(self):
        self.volume_manager.toplevel_mount = mock.Mock()
        volume_mount = mock.Mock()
        volume_mount.is_mounted = mock.Mock(
            return_value=True
        )
        self.volume_manager.toplevel_mount.is_mounted = mock.Mock(
            return_value=True
        )
        self.volume_manager.subvol_mount_list = [volume_mount]
        self.volume_manager.umount_volumes()
        volume_mount.is_mounted.assert_called_once_with()
        volume_mount.umount.assert_called_once_with()
        self.volume_manager.toplevel_mount.is_mounted.assert_called_once_with()
        self.volume_manager.toplevel_mount.umount.assert_called_once_with()

    def test_umount_sub_volumes_busy(self):
        self.volume_manager.toplevel_mount = mock.Mock()
        volume_mount = mock.Mock()
        volume_mount.is_mounted = mock.Mock(
            return_value=True
        )
        volume_mount.umount = mock.Mock(
            return_value=False
        )
        self.volume_manager.subvol_mount_list = [volume_mount]
        assert self.volume_manager.umount_volumes() is False

    def test_umount_toplevel_busy(self):
        self.volume_manager.toplevel_mount = mock.Mock()
        volume_mount = mock.Mock()
        volume_mount.is_mounted = mock.Mock(
            return_value=True
        )
        self.volume_manager.toplevel_mount.is_mounted = mock.Mock(
            return_value=True
        )
        self.volume_manager.toplevel_mount.umount = mock.Mock(
            return_value=False
        )
        assert self.volume_manager.umount_volumes() is False

    @patch_open
    @patch('kiwi.volume_manager.btrfs.SysConfig')
    @patch('kiwi.volume_manager.btrfs.DataSync')
    @patch('kiwi.volume_manager.btrfs.Command.run')
    @patch('os.path.exists')
    @patch('shutil.copyfile')
    @patch.object(datetime, 'datetime', mock.Mock(wraps=datetime.datetime))
    def test_sync_data(
        self, mock_copy, mock_exists, mock_command,
        mock_sync, mock_sysconf, mock_open
    ):
        item = {'SNAPPER_CONFIGS': '""'}

        def getitem(key):
            return item[key]

        def setitem(key, value):
            item[key] = value

        def contains(key):
            return key in item

        def exists(name):
            if 'snapper/configs/root' in name:
                return False
            return True

        self.volume_manager.custom_args['quota_groups'] = True
        mock_exists.side_effect = exists

        sysconf = mock.Mock()
        sysconf.__contains__ = mock.Mock(side_effect=contains)
        sysconf.__getitem__ = mock.Mock(side_effect=getitem)
        sysconf.__setitem__ = mock.Mock(side_effect=setitem)
        mock_sysconf.return_value = sysconf

        xml_info = etree.tostring(etree.parse(
            '../data/info.xml', etree.XMLParser(remove_blank_text=True)
        ))
        datetime.datetime.now.return_value = datetime.datetime(2016, 1, 1)
        mock_open.return_value = self.context_manager_mock
        self.volume_manager.toplevel_mount = mock.Mock()
        self.volume_manager.mountpoint = 'tmpdir'
        self.volume_manager.custom_args['root_is_snapshot'] = True
        sync = mock.Mock()
        mock_sync.return_value = sync

        self.volume_manager.sync_data(['exclude_me'])

        root_path = 'tmpdir/@/.snapshots/1/snapshot'
        mock_sync.assert_called_once_with('root_dir', root_path)
        mock_copy.assert_called_once_with(
            root_path + '/etc/snapper/config-templates/default',
            root_path + '/etc/snapper/configs/root'
        )
        sync.sync_data.assert_called_once_with(
            exclude=['exclude_me'],
            options=['-a', '-H', '-X', '-A', '--one-file-system']
        )
        assert mock_open.call_args_list == [
            call('tmpdir/@/.snapshots/1/info.xml', 'w'),
        ]
        assert self.file_mock.write.call_args_list == [
            call(minidom.parseString(xml_info).toprettyxml(indent="    "))
        ]
        assert mock_command.call_args_list == [
            call(['btrfs', 'qgroup', 'create', '1/0', 'tmpdir']),
            call([
                'chroot', 'tmpdir/@/.snapshots/1/snapshot',
                'snapper', '--no-dbus', 'set-config', 'QGROUP=1/0'
            ])
        ]

    @raises(KiwiVolumeManagerSetupError)
    @patch_open
    @patch('kiwi.volume_manager.btrfs.SysConfig')
    @patch('kiwi.volume_manager.btrfs.DataSync')
    @patch('kiwi.volume_manager.btrfs.Command.run')
    @patch('os.path.exists')
    @patch.object(datetime, 'datetime', mock.Mock(wraps=datetime.datetime))
    def test_sync_data_existing_bad_snapper_config(
        self, mock_exists, mock_command, mock_sync, mock_sysconf, mock_open
    ):
        item = {'SNAPPER_CONFIGS': '"root foo"'}

        def getitem(key):
            return item[key]

        def contains(key):
            return key in item

        sysconf = mock.Mock()
        sysconf.__contains__ = mock.Mock(side_effect=contains)
        sysconf.__getitem__ = mock.Mock(side_effect=getitem)
        mock_sysconf.return_value = sysconf

        self.volume_manager.custom_args['quota_groups'] = True
        mock_exists.return_value = True
        xml_info = etree.tostring(etree.parse(
            '../data/info.xml', etree.XMLParser(remove_blank_text=True)
        ))
        datetime.datetime.now.return_value = datetime.datetime(2016, 1, 1)
        mock_open.return_value = self.context_manager_mock
        self.volume_manager.toplevel_mount = mock.Mock()
        self.volume_manager.mountpoint = 'tmpdir'
        self.volume_manager.custom_args['root_is_snapshot'] = True
        sync = mock.Mock()
        mock_sync.return_value = sync

        self.volume_manager.sync_data(['exclude_me'])

        mock_sync.assert_called_once_with(
            'root_dir', 'tmpdir/@/.snapshots/1/snapshot'
        )
        sync.sync_data.assert_called_once_with(
            exclude=['exclude_me'],
            options=['-a', '-H', '-X', '-A', '--one-file-system']
        )
        assert mock_open.call_args_list == [
            call('tmpdir/@/.snapshots/1/info.xml', 'w'),
        ]
        assert self.file_mock.write.call_args_list == [
            call(minidom.parseString(xml_info).toprettyxml(indent="    "))
        ]

    @patch('kiwi.volume_manager.btrfs.DataSync')
    @patch('kiwi.volume_manager.btrfs.Command.run')
    @patch('os.path.exists')
    @patch.object(datetime, 'datetime', mock.Mock(wraps=datetime.datetime))
    def test_sync_data_no_root_snapshot(
        self, mock_exists, mock_command, mock_sync
    ):
        self.volume_manager.custom_args['quota_groups'] = True
        mock_exists.return_value = True
        datetime.datetime.now.return_value = datetime.datetime(2016, 1, 1)
        self.file_mock.readlines = mock.Mock(
            return_value=[]
        )
        self.volume_manager.toplevel_mount = mock.Mock()
        self.volume_manager.mountpoint = 'tmpdir'
        self.volume_manager.custom_args['root_is_snapshot'] = False
        sync = mock.Mock()
        mock_sync.return_value = sync

        self.volume_manager.sync_data(['exclude_me'])

        mock_sync.assert_called_once_with(
            'root_dir', 'tmpdir/@'
        )
        sync.sync_data.assert_called_once_with(
            exclude=['exclude_me'],
            options=['-a', '-H', '-X', '-A', '--one-file-system']
        )

    @patch('kiwi.volume_manager.btrfs.Command.run')
    def test_set_property_readonly_root(self, mock_command):
        self.volume_manager.mountpoint = 'tmpdir'
        self.volume_manager.custom_args['root_is_snapshot'] = True
        self.volume_manager.custom_args['root_is_readonly_snapshot'] = True
        self.volume_manager.set_property_readonly_root()
        mock_command.assert_called_once_with(
            [
                'btrfs', 'property', 'set', 'tmpdir', 'ro', 'true'
            ]
        )

    @patch('kiwi.volume_manager.btrfs.VolumeManagerBtrfs.umount_volumes')
    @patch('kiwi.volume_manager.btrfs.Path.wipe')
    def test_destructor(self, mock_wipe, mock_umount_volumes):
        mock_umount_volumes.return_value = True
        self.volume_manager.toplevel_mount = mock.Mock()
        self.volume_manager.__del__()
        mock_umount_volumes.assert_called_once_with()
        mock_wipe.assert_called_once_with(self.volume_manager.mountpoint)
