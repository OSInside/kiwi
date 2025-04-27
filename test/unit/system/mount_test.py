import os
from unittest.mock import (
    patch, MagicMock, Mock, call
)
from pytest import fixture

from kiwi.system.mount import ImageSystem
from kiwi.storage.mapped_device import MappedDevice
from kiwi.storage.disk import ptable_entry_type


class TestImageSystem:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    @patch('os.path.exists')
    def setup(self, mock_os_path_exists):
        mock_os_path_exists.return_value = True
        self.device_map = {
            'root': MappedDevice('/dev/root-device', Mock()),
            'readonly': MappedDevice('/dev/readonly-root-device', Mock()),
            'boot': MappedDevice('/dev/boot-device', Mock()),
            'efi': MappedDevice('/dev/efi-device', Mock()),
            'var': MappedDevice('/dev/var-device', Mock())
        }
        volume_manager = Mock()
        volume_manager.get_mountpoint.return_value = 'volume_manager_root'
        self.volume_manager = volume_manager
        self.partitions = {
            'var': ptable_entry_type(
                mbsize=100,
                clone=1,
                partition_name='p.lxvar',
                partition_type='t.linux',
                mountpoint='/var',
                filesystem='ext3'
            )
        }
        self.image_system = ImageSystem(
            self.device_map, 'root_dir', self.volume_manager, self.partitions
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_os_path_exists):
        self.setup()

    def test_mountpoint(self):
        assert self.image_system.mountpoint() == ''

    @patch('kiwi.system.mount.MountManager')
    def test_mount_with_volumes(self, mock_MountManager):
        self.image_system.mount()
        root_mount_mountpoint = self.image_system.mountpoint()
        self.volume_manager.mount_volumes.assert_called_once_with()
        assert mock_MountManager.call_args_list == [
            call(
                device='/dev/boot-device',
                mountpoint=os.path.join(root_mount_mountpoint, 'boot')
            ),
            call(
                device='/dev/efi-device',
                mountpoint=os.path.join(root_mount_mountpoint, 'boot', 'efi')
            ),
            call(
                device='/dev/var-device',
                mountpoint=os.path.join(root_mount_mountpoint, 'var')
            ),
            call(
                device='root_dir/image',
                mountpoint=os.path.join(root_mount_mountpoint, 'image')
            ),
            call(
                device='tmpfs',
                mountpoint=os.path.join(root_mount_mountpoint, 'tmp')
            ),
            call(
                device='tmpfs',
                mountpoint=os.path.join(root_mount_mountpoint, 'var', 'tmp')
            ),
            call(
                device='/proc',
                mountpoint=os.path.join(root_mount_mountpoint, 'proc')
            ),
            call(
                device='/sys',
                mountpoint=os.path.join(root_mount_mountpoint, 'sys')
            ),
            call(
                device='/dev',
                mountpoint=os.path.join(root_mount_mountpoint, 'dev')
            )
        ]

    @patch('kiwi.system.mount.MountManager')
    def test_mount(self, mock_MountManager):
        self.image_system.volume_manager = None
        self.image_system.mount()
        root_mount_mountpoint = self.image_system.mountpoint()
        assert mock_MountManager.call_args_list == [
            call(device='/dev/readonly-root-device'),
            call(
                device='/dev/boot-device',
                mountpoint=os.path.join(root_mount_mountpoint, 'boot')
            ),
            call(
                device='/dev/efi-device',
                mountpoint=os.path.join(root_mount_mountpoint, 'boot', 'efi')
            ),
            call(
                device='/dev/var-device',
                mountpoint=os.path.join(root_mount_mountpoint, 'var')
            ),
            call(
                device='root_dir/image',
                mountpoint=os.path.join(root_mount_mountpoint, 'image')
            ),
            call(
                device='tmpfs',
                mountpoint=os.path.join(root_mount_mountpoint, 'tmp')
            ),
            call(
                device='tmpfs',
                mountpoint=os.path.join(root_mount_mountpoint, 'var', 'tmp')
            ),
            call(
                device='/proc',
                mountpoint=os.path.join(root_mount_mountpoint, 'proc')
            ),
            call(
                device='/sys',
                mountpoint=os.path.join(root_mount_mountpoint, 'sys')
            ),
            call(
                device='/dev',
                mountpoint=os.path.join(root_mount_mountpoint, 'dev')
            )
        ]

    @patch('kiwi.system.mount.MountManager')
    def test_mount_s390(self, mock_MountManager):
        self.image_system.arch = 's390x'
        self.image_system.mount()
        root_mount_mountpoint = self.image_system.mountpoint()
        assert mock_MountManager.call_args_list[0] == call(
            device='/dev/boot-device',
            mountpoint=os.path.join(root_mount_mountpoint, 'boot', 'zipl')
        )

    def test_umount(self):
        some_mount = MagicMock()
        some_mount.is_mounted.return_value = True
        self.image_system.mount_list.append(some_mount)
        self.image_system.umount()
        some_mount.umount.assert_called_once_with()

    @patch('os.path.exists')
    @patch('kiwi.system.mount.MountManager')
    def test_context_manager_exit(self, mock_MountManager, mock_os_path_exists):
        mount = MagicMock()
        mount.is_mounted.return_value = True
        mock_os_path_exists.return_value = True
        mock_MountManager.return_value = mount
        device_map = {
            'root': MappedDevice('/dev/root-device', Mock())
        }
        with ImageSystem(device_map, 'root_dir') as system:
            system.mount()
        mount.umount.assert_called()
