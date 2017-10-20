from mock import patch

import mock

from .test_helper import raises

from collections import namedtuple
from kiwi.exceptions import KiwiVolumeManagerSetupError
from kiwi.volume_manager.base import VolumeManagerBase


class TestVolumeManagerBase(object):
    @patch('os.path.exists')
    def setup(self, mock_path):
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
        mock_path.return_value = True
        self.device_provider = mock.Mock()
        self.device_provider.is_loop = mock.Mock(
            return_value=True
        )
        self.device_provider.get_device = mock.Mock(
            return_value='/dev/storage'
        )
        self.volume_manager = VolumeManagerBase(
            self.device_provider, 'root_dir', mock.Mock()
        )
        self.volume_manager.volumes = [
            self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False, attributes=[]
            ),
            self.volume_type(
                name='LVRoot', size='size:500', realpath='/',
                mountpoint='/', fullsize=True, attributes=[]
            )
        ]

    @patch('os.path.exists')
    def test_init_custom_args(self, mock_exists):
        mock_exists.return_value = True
        volume_manager = VolumeManagerBase(
            mock.Mock(), 'root_dir', mock.Mock(),
            {
                'fs_create_options': 'create-opts',
                'fs_mount_options': 'mount-opts'
            }
        )
        assert volume_manager.custom_filesystem_args['mount_options'] == \
            'mount-opts'
        assert volume_manager.custom_filesystem_args['create_options'] == \
            'create-opts'

    @patch('os.path.exists')
    @raises(KiwiVolumeManagerSetupError)
    def test_root_dir_does_not_exist(self, mock_exists):
        mock_exists.return_value = False
        VolumeManagerBase(mock.Mock(), 'root_dir', mock.Mock())

    def test_is_loop(self):
        assert self.volume_manager.is_loop() == \
            self.device_provider.is_loop()

    @patch('os.path.exists')
    def test_get_device(self, mock_exists):
        mock_exists.return_value = True
        assert self.volume_manager.get_device()['root'].get_device() == \
            '/dev/storage'

    @raises(NotImplementedError)
    def test_setup(self):
        self.volume_manager.setup()

    @raises(NotImplementedError)
    def test_create_volumes(self):
        self.volume_manager.create_volumes('ext3')

    @raises(NotImplementedError)
    def test_get_fstab(self):
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
    def test_get_volume_mbsize(self, mock_size):
        size = mock.Mock()
        size.customize = mock.Mock(
            return_value=42
        )
        mock_size.return_value = size
        assert self.volume_manager.get_volume_mbsize(
            self.volume_manager.volumes[0], self.volume_manager.volumes,
            'ext3'
        ) == 272

    @patch('kiwi.volume_manager.base.SystemSize')
    def test_get_volume_mbsize_for_oem_type(self, mock_size):
        size = mock.Mock()
        size.customize = mock.Mock(
            return_value=42
        )
        mock_size.return_value = size
        assert self.volume_manager.get_volume_mbsize(
            self.volume_manager.volumes[0], self.volume_manager.volumes,
            'ext3', 'oem'
        ) == 72

    @patch('kiwi.volume_manager.base.SystemSize')
    def test_get_volume_mbsize_nested_volumes(self, mock_size):
        size = mock.Mock()
        size.customize = mock.Mock(
            return_value=42
        )
        mock_size.return_value = size
        self.volume_manager.volumes = [
            self.volume_type(
                name='LVusr', size='freespace:200', realpath='/usr',
                mountpoint='/usr', fullsize=False, attributes=[]
            ),
            self.volume_type(
                name='LVusr_lib', size='freespace:100', realpath='/usr/lib',
                mountpoint='/usr/lib', fullsize=False, attributes=[]
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
    def test_get_volume_mbsize_root_volume(self, mock_size):
        size = mock.Mock()
        size.customize = mock.Mock(
            return_value=42
        )
        mock_size.return_value = size
        self.volume_manager.volumes = [
            self.volume_type(
                name='LVusr', size='freespace:200', realpath='/usr',
                mountpoint='/usr', fullsize=False, attributes=[]
            ),
            self.volume_type(
                name='LVusr_lib', size='freespace:100', realpath='/usr/lib',
                mountpoint='/usr/lib', fullsize=False, attributes=[]
            ),
            self.volume_type(
                name='LVRoot', size='size:500', realpath='/',
                mountpoint='/', fullsize=True, attributes=[]
            )
        ]
        assert self.volume_manager.get_volume_mbsize(
            self.volume_manager.volumes[2], self.volume_manager.volumes,
            'ext3', 'oem'
        ) == 72
        size.accumulate_mbyte_file_sizes.assert_called_once_with(
            ['root_dir/usr', 'root_dir/usr/lib']
        )

    @raises(NotImplementedError)
    def test_mount_volumes(self):
        self.volume_manager.mount_volumes()

    @raises(NotImplementedError)
    def test_umount_volumes(self):
        self.volume_manager.umount_volumes()

    @raises(NotImplementedError)
    def test_get_volumes(self):
        self.volume_manager.get_volumes()

    @patch('kiwi.volume_manager.base.DataSync')
    @patch('kiwi.volume_manager.base.MountManager.is_mounted')
    @patch('kiwi.volume_manager.base.VolumeManagerBase.mount_volumes')
    @patch('kiwi.volume_manager.base.VolumeManagerBase.umount_volumes')
    def test_sync_data(
        self, mock_umount_volumes, mock_mount_volumes, mock_mounted, mock_sync
    ):
        data_sync = mock.Mock()
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
            options=['-a', '-H', '-X', '-A', '--one-file-system']
        )
        mock_umount_volumes.assert_called_once_with()

    @patch('kiwi.volume_manager.base.mkdtemp')
    def test_setup_mountpoint(self, mock_mkdtemp):
        mock_mkdtemp.return_value = 'tmpdir'
        self.volume_manager.setup_mountpoint()
        assert self.volume_manager.mountpoint == 'tmpdir'

    @raises(KiwiVolumeManagerSetupError)
    def test_set_property_readonly_root(self):
        self.volume_manager.set_property_readonly_root()

    @patch('kiwi.volume_manager.base.Command.run')
    def test_apply_attributes_on_volume(self, mock_command):
        self.volume_manager.apply_attributes_on_volume(
            'toplevel', self.volume_type(
                name='LVetc', size='freespace:200', realpath='/etc',
                mountpoint='/etc', fullsize=False,
                attributes=['no-copy-on-write']
            )
        )
        mock_command.assert_called_once_with(
            ['chattr', '+C', 'toplevel/etc']
        )

    def test_destructor(self):
        # does nothing by default, just pass
        self.volume_manager.__del__()
