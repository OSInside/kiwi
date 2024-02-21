from collections import namedtuple
from unittest.mock import (
    patch, Mock
)
from pytest import raises

from kiwi.volume_manager.base import VolumeManagerBase

from kiwi.exceptions import KiwiVolumeManagerSetupError


class TestVolumeManagerBase:
    @patch('os.path.exists')
    def setup(self, mock_path):
        self.volume_type = namedtuple(
            'volume_type', [
                'name',
                'size',
                'realpath',
                'mountpoint',
                'fullsize',
                'attributes',
                'is_root_volume'
            ]
        )
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
        self.volume_manager = VolumeManagerBase(
            self.device_map, 'root_dir', Mock()
        )
        self.volume_manager.volumes = [
            self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False, attributes=[],
                is_root_volume=False
            ),
            self.volume_type(
                name='LVRoot', size='size:500', realpath='/',
                mountpoint='/', fullsize=True, attributes=[],
                is_root_volume=True
            )
        ]

    @patch('os.path.exists')
    def setup_method(self, cls, mock_path):
        self.setup()

    def test_get_root_volume_name(self):
        assert self.volume_manager.get_root_volume_name() == '/'

    @patch('os.path.exists')
    def test_init_custom_args(self, mock_exists):
        mock_exists.return_value = True
        volume_manager = VolumeManagerBase(
            self.device_map, 'root_dir', Mock(), {
                'fs_create_options': 'create-opts',
                'fs_mount_options': 'mount-opts'
            }
        )
        assert volume_manager.custom_filesystem_args['mount_options'] == \
            'mount-opts'
        assert volume_manager.custom_filesystem_args['create_options'] == \
            'create-opts'

    @patch('os.path.exists')
    def test_root_dir_does_not_exist(self, mock_exists):
        mock_exists.return_value = False
        with raises(KiwiVolumeManagerSetupError):
            VolumeManagerBase(self.device_map, 'root_dir', Mock())

    def test_is_loop(self):
        assert self.volume_manager.is_loop() == \
            self.device_map['root'].is_loop()

    @patch('os.path.exists')
    def test_get_device(self, mock_exists):
        mock_exists.return_value = True
        assert self.volume_manager.get_device()['root'].get_device() == \
            '/dev/storage'

    def test_setup(self):
        with raises(NotImplementedError):
            self.volume_manager.setup()

    def test_create_volumes(self):
        with raises(NotImplementedError):
            self.volume_manager.create_volumes('ext3')

    def test_get_fstab(self):
        with raises(NotImplementedError):
            self.volume_manager.get_fstab('by-label', 'ext3')

    @patch('kiwi.volume_manager.base.Path.create')
    @patch('os.path.exists')
    def test_create_volume_paths_in_root_dir(self, mock_os_path, mock_path):
        mock_os_path.return_value = False
        self.volume_manager.create_volume_paths_in_root_dir()
        mock_path.assert_called_once_with('root_dir/etc')

    def test_get_canonical_volume_list(self):
        volume_list = self.volume_manager.get_canonical_volume_list()
        assert volume_list.volumes[0].name == 'LVetc'
        assert volume_list.full_size_volume.name == 'LVRoot'

    @patch('kiwi.volume_manager.base.SystemSize')
    @patch('os.path.exists')
    def test_get_volume_mbsize(
        self, mock_os_path_exists, mock_size
    ):
        mock_os_path_exists.return_value = True
        size = Mock()
        size.customize = Mock(
            return_value=42
        )
        mock_size.return_value = size
        assert self.volume_manager.get_volume_mbsize(
            self.volume_manager.volumes[0], self.volume_manager.volumes,
            'ext3'
        ) == 272

    @patch('kiwi.volume_manager.base.SystemSize')
    @patch('os.path.exists')
    def test_get_volume_mbsize_for_oem_type(
        self, mock_os_path_exists, mock_size
    ):
        mock_os_path_exists.return_value = True
        size = Mock()
        size.customize = Mock(
            return_value=42
        )
        mock_size.return_value = size
        assert self.volume_manager.get_volume_mbsize(
            self.volume_manager.volumes[0], self.volume_manager.volumes,
            'ext3', True
        ) == 72

    @patch('kiwi.volume_manager.base.SystemSize')
    @patch('os.path.exists')
    def test_get_volume_mbsize_nested_volumes(
        self, mock_os_path_exists, mock_size
    ):
        mock_os_path_exists.return_value = True
        size = Mock()
        size.customize = Mock(
            return_value=42
        )
        mock_size.return_value = size
        self.volume_manager.volumes = [
            self.volume_type(
                name='LVusr', size='freespace:200', realpath='/usr',
                mountpoint='/usr', fullsize=False, attributes=[],
                is_root_volume=False
            ),
            self.volume_type(
                name='LVusr_lib', size='freespace:100', realpath='/usr/lib',
                mountpoint='/usr/lib', fullsize=False, attributes=[],
                is_root_volume=False
            )
        ]
        assert self.volume_manager.get_volume_mbsize(
            self.volume_manager.volumes[0], self.volume_manager.volumes,
            'ext3'
        ) == 272
        size.accumulate_mbyte_file_sizes.assert_called_once_with(
            ['root_dir/usr/lib']
        )

    @patch('kiwi.volume_manager.base.SystemSize')
    @patch('os.path.exists')
    def test_get_volume_mbsize_root_volume(
        self, mock_os_path_exists, mock_size
    ):
        mock_os_path_exists.return_value = True
        size = Mock()
        size.customize = Mock(
            return_value=42
        )
        mock_size.return_value = size
        self.volume_manager.volumes = [
            self.volume_type(
                name='LVusr', size='freespace:200', realpath='/usr',
                mountpoint='/usr', fullsize=False, attributes=[],
                is_root_volume=False
            ),
            self.volume_type(
                name='LVusr_lib', size='freespace:100', realpath='/usr/lib',
                mountpoint='/usr/lib', fullsize=False, attributes=[],
                is_root_volume=False
            ),
            self.volume_type(
                name='LVRoot', size='size:500', realpath='/',
                mountpoint='/', fullsize=True, attributes=[],
                is_root_volume=True
            )
        ]
        assert self.volume_manager.get_volume_mbsize(
            self.volume_manager.volumes[2], self.volume_manager.volumes,
            'ext3', True
        ) == 72
        size.accumulate_mbyte_file_sizes.assert_called_once_with(
            ['root_dir/usr', 'root_dir/usr/lib']
        )

    def test_mount_volumes(self):
        with raises(NotImplementedError):
            self.volume_manager.mount_volumes()

    def test_mount(self):
        with raises(NotImplementedError):
            self.volume_manager.mount()

    def test_umount_volumes(self):
        with raises(NotImplementedError):
            self.volume_manager.umount_volumes()

    def test_umount(self):
        with raises(NotImplementedError):
            self.volume_manager.umount()

    def test_get_volumes(self):
        with raises(NotImplementedError):
            self.volume_manager.get_volumes()

    def test_get_mountpoint(self):
        assert self.volume_manager.get_mountpoint() is None

    @patch('kiwi.volume_manager.base.DataSync')
    @patch('kiwi.volume_manager.base.MountManager.is_mounted')
    @patch('kiwi.volume_manager.base.VolumeManagerBase.mount_volumes')
    def test_sync_data(self, mock_mount_volumes, mock_mounted, mock_sync):
        data_sync = Mock()
        mock_sync.return_value = data_sync
        mock_mounted.return_value = False
        self.volume_manager.mountpoint = 'mountpoint'
        self.volume_manager.sync_data(['exclude_me'])
        mock_mount_volumes.assert_called_once_with()
        mock_sync.assert_called_once_with(
            'root_dir', 'mountpoint'
        )
        data_sync.sync_data.assert_called_once_with(
            exclude=['exclude_me'],
            options=[
                '--archive', '--hard-links', '--xattrs',
                '--acls', '--one-file-system', '--inplace'
            ]
        )
        assert self.volume_manager.get_mountpoint() == 'mountpoint'

    @patch('kiwi.volume_manager.base.MountManager.is_mounted')
    def test_sync_data_without_mountpoint(self, mock_mounted):
        self.volume_manager.mountpoint = ''
        assert self.volume_manager.sync_data() is None
        mock_mounted.assert_not_called()

    def test_create_verity_layer(self):
        with raises(NotImplementedError):
            self.volume_manager.create_verity_layer()

    def test_create_verification_metadata(self):
        with raises(NotImplementedError):
            self.volume_manager.create_verification_metadata('/some/device')

    @patch('kiwi.volume_manager.base.Temporary')
    def test_setup_mountpoint(self, mock_Temporary):
        mock_Temporary.return_value.new_dir.return_value.name = 'tmpdir'
        self.volume_manager.setup_mountpoint()
        assert self.volume_manager.mountpoint == 'tmpdir'

    def test_set_property_readonly_root(self):
        with raises(KiwiVolumeManagerSetupError):
            self.volume_manager.set_property_readonly_root()

    @patch('kiwi.volume_manager.base.Command.run')
    def test_apply_attributes_on_volume(self, mock_command):
        self.volume_manager.apply_attributes_on_volume(
            'toplevel', self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False,
                attributes=['no-copy-on-write'],
                is_root_volume=False
            )
        )
        mock_command.assert_called_once_with(
            ['chattr', '+C', 'toplevel/etc']
        )

    @patch('os.path.exists')
    def test_context_manager_exit(self, mock_os_path_exists):
        mock_os_path_exists.return_value = True
        with VolumeManagerBase(self.device_map, 'root_dir', Mock()):
            pass
            # just pass
