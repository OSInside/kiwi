import os
import logging
from unittest.mock import (
    patch, MagicMock, Mock, call
)
from pytest import fixture

from kiwi.system.mount import ImageSystem
from kiwi.storage.mapped_device import MappedDevice


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
        }
        self.volumes = {
            'name': {
                'volume_options': 'a,b,c',
                'volume_device': '/dev/vgroup/volume'
            }
        }
        self.image_system = ImageSystem(
            self.device_map, 'root_dir', self.volumes
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_os_path_exists):
        self.setup()

    def test_mountpoint(self):
        some_mount = MagicMock()
        self.image_system.mount_list.append(some_mount)
        assert self.image_system.mountpoint() == some_mount.mountpoint

    @patch('kiwi.system.mount.MountManager')
    def test_mount(self, mock_MountManager):
        self.image_system.mount()
        root_mount_mountpoint = self.image_system.mount_list[0].mountpoint
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
                device='/dev/vgroup/volume',
                mountpoint=os.path.join(root_mount_mountpoint, 'name')
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
        root_mount_mountpoint = self.image_system.mount_list[0].mountpoint
        assert mock_MountManager.call_args_list[1] == call(
            device='/dev/boot-device',
            mountpoint=os.path.join(root_mount_mountpoint, 'boot', 'zipl')
        )

    def test_umount(self):
        some_mount = MagicMock()
        some_mount.is_mounted.return_value = True
        self.image_system.mount_list.append(some_mount)
        self.image_system.umount()
        some_mount.umount.assert_called_once_with()

    def test_destructor(self):
        some_mount = MagicMock()
        some_mount.is_mounted.return_value = True
        self.image_system.mount_list.append(some_mount)
        with self._caplog.at_level(logging.INFO):
            self.image_system.__del__()
        some_mount.umount.assert_called_once_with()
