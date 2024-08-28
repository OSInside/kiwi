# Copyright (c) 2022 Marcus Schäfer.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import os
import logging
from typing import (
    List, Dict
)

# project
from kiwi.path import Path
from kiwi.defaults import Defaults
from kiwi.mount_manager import MountManager

log = logging.getLogger('kiwi')


class ImageSystem:
    """
    **Access the target image from the block layer**
    """
    def __init__(
        self, device_map: Dict, root_dir: str, volumes: Dict = {}
    ) -> None:
        """
        Construct a new ImageSystem object

        :param dict device_map: Block device map
        :param str root_dir: Path to unpacked image root tree
        :param list volumes: Optional list of filesystem volumes
        """
        self.arch = Defaults.get_platform_name()
        self.device_map = device_map
        self.root_dir = root_dir
        self.volumes = volumes
        self.mount_list: List[MountManager] = []

    def __enter__(self):
        return self

    def mountpoint(self) -> str:
        """
        Return image root mountpoint

        :return: mountpoint path or empty string

        :rtype: str
        """
        mountpoint = ''
        if self.mount_list:
            mountpoint = self.mount_list[0].mountpoint
        return mountpoint

    def mount(self) -> None:
        """
        Mount image system from current block layers
        """
        # mount root boot and efi devices as they are present
        (root_device, boot_device, efi_device, other_devices) = self._setup_device_names()
        root_mount = MountManager(
            device=root_device
        )
        if 's390' in self.arch:
            boot_mount = MountManager(
                device=boot_device, mountpoint=os.path.join(
                    root_mount.mountpoint, 'boot', 'zipl'
                )
            )
        else:
            boot_mount = MountManager(
                device=boot_device, mountpoint=os.path.join(
                    root_mount.mountpoint, 'boot'
                )
            )
        if efi_device:
            efi_mount = MountManager(
                device=efi_device, mountpoint=os.path.join(
                    root_mount.mountpoint, 'boot', 'efi'
                )
            )
        other_mounts = [
            MountManager(
                device=d, mountpoint=os.path.join(
                    root_mount.mountpoint, m)) for (m, d) in other_devices.items()
        ]

        self.mount_list.append(root_mount)
        root_mount.mount()

        if not root_mount.device == boot_mount.device:
            self.mount_list.append(boot_mount)
            boot_mount.mount()

        if efi_device:
            self.mount_list.append(efi_mount)
            efi_mount.mount()

        for mount in other_mounts:
            self.mount_list.append(mount)
            mount.mount()

        if self.volumes:
            self._mount_volumes(root_mount.mountpoint)

        # bind mount /image from unpacked root to get access to e.g scripts
        image_mount = MountManager(
            device=os.path.join(self.root_dir, 'image'),
            mountpoint=os.path.join(
                root_mount.mountpoint, 'image'
            )
        )
        self.mount_list.append(image_mount)
        image_mount.bind_mount()

        # mount tmp as tmpfs
        tmp_mount = MountManager(
            device='tmpfs', mountpoint=os.path.join(
                root_mount.mountpoint, 'tmp'
            )
        )
        self.mount_list.append(tmp_mount)
        tmp_mount.tmpfs_mount()

        # mount var/tmp as tmpfs
        var_tmp_mount = MountManager(
            device='tmpfs', mountpoint=os.path.join(
                root_mount.mountpoint, 'var', 'tmp'
            )
        )
        self.mount_list.append(var_tmp_mount)
        var_tmp_mount.tmpfs_mount()

        # mount kernel interfaces as bind
        for location in ('proc', 'sys', 'dev'):
            shared_mount = MountManager(
                device=os.path.join('/', location), mountpoint=os.path.join(
                    root_mount.mountpoint, location
                )
            )
            self.mount_list.append(shared_mount)
            shared_mount.bind_mount()

    def umount(self) -> None:
        """
        Umount all elements of mount_list in reverse order
        """
        for mount in reversed(self.mount_list):
            if mount.is_mounted():
                mount.umount()

    def _setup_device_names(self) -> tuple:
        root_device = self.device_map['root'].get_device()
        boot_device = root_device
        efi_device = None
        if 'boot' in self.device_map:
            boot_device = self.device_map['boot'].get_device()
        if 'readonly' in self.device_map:
            root_device = self.device_map['readonly'].get_device()
        if 'efi' in self.device_map:
            efi_device = self.device_map['efi'].get_device()
        other_devices = {
            d: self.device_map[d].get_device() for d in self.device_map if d not in (
                'root', 'origin_root', 'boot', 'readonly', 'efi', 'efi_csm', 'swap'
            ) and self.device_map[d]
        }
        return (root_device, boot_device, efi_device, other_devices)

    def _mount_volumes(self, mountpoint) -> None:
        for volume_path in Path.sort_by_hierarchy(sorted(self.volumes.keys())):
            volume_mount = MountManager(
                device=self.volumes[volume_path]['volume_device'],
                mountpoint=os.path.join(
                    mountpoint, volume_path.lstrip(os.sep)
                )
            )
            self.mount_list.append(volume_mount)
            volume_mount.mount(
                options=[self.volumes[volume_path]['volume_options']]
            )

    def __exit__(self, exc_type, exc_value, traceback):
        self.umount()
