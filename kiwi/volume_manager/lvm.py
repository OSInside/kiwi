# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
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
    Dict, List
)

# project
import kiwi.defaults as defaults

from kiwi.volume_manager.base import VolumeManagerBase
from kiwi.command import Command
from kiwi.mount_manager import MountManager
from kiwi.storage.mapped_device import MappedDevice
from kiwi.filesystem import FileSystem
from kiwi.path import Path

from kiwi.exceptions import (
    KiwiVolumeGroupConflict,
    KiwiCommandError
)

log = logging.getLogger('kiwi')


class VolumeManagerLVM(VolumeManagerBase):
    """
    **Implements LVM volume management**
    """
    def post_init(self, custom_args):
        """
        Post initialization method

        Store custom lvm initialization arguments

        :param list custom_args: custom lvm volume manager arguments
        """
        if custom_args:
            self.custom_args = custom_args
        else:
            self.custom_args = {}
        if 'root_label' not in self.custom_args:
            self.custom_args['root_label'] = 'ROOT'
        if 'resize_on_boot' not in self.custom_args:
            self.custom_args['resize_on_boot'] = False

        if self.custom_filesystem_args['mount_options']:
            self.mount_options = self.custom_filesystem_args['mount_options'][0]
        else:
            self.mount_options = 'defaults'

        self.lvm_tool_options = [
            '--config', 'devices/external_device_info_source=none'
        ]

    def get_device(self):
        """
        Dictionary of MappedDevice instances per volume

        Note: The mapping requires an explicit create_volumes() call

        :return: root plus volume device map

        :rtype: dict
        """
        device_map = {}
        for volume_name, volume_node in list(self.volume_map.items()):
            if self._is_root_volume(volume_name):
                # root volume device takes precedence over the
                # root partition device from the disk. Therefore use
                # the same key to put them on the same level
                volume_name = 'root'
            if self._is_swap_volume(volume_name):
                # swap volume device takes precedence over the
                # swap partition device from the disk. Therefore use
                # the same key to put them on the same level
                volume_name = 'swap'
            device_map[volume_name] = MappedDevice(
                device=volume_node, device_provider=self.device_provider_root
            )
        return device_map

    def setup(self, volume_group_name='systemVG'):
        """
        Setup lvm volume management

        In case of LVM a new volume group is created on a PV
        initialized storage device

        :param str name: volume group name
        """
        self.setup_mountpoint()

        if self._volume_group_in_use_on_host_system(volume_group_name):
            raise KiwiVolumeGroupConflict(
                f'Requested volume group {volume_group_name} is in use on this host'
            )
        log.info(
            'Creating volume group %s', volume_group_name
        )
        Command.run(
            command=['vgremove'] + self.lvm_tool_options + [
                '--force', volume_group_name
            ], raise_on_error=False
        )
        Command.run(
            ['pvcreate'] + self.lvm_tool_options + [self.device]
        )
        Command.run(
            ['vgcreate'] + self.lvm_tool_options + [
                volume_group_name, self.device
            ]
        )
        self.volume_group = volume_group_name

    @staticmethod
    def _create_volume_no_zero(lvm_tool_options, lvcreate_args):
        """
        Create an LV using specified arguments to lvcreate

        The LV will be created with the '-Zn' option prepended
        to the arguments, which disables the zeroing of the new
        device's header; this action will fail when running in
        an environment where udev is not enabled, such as in a
        chroot'd Open Build Service build. Since the backing
        device for a kiwi LVM device is a zero filled qemu-img
        created file, there should be no negative side effects
        to skipping the zeroing of this header block.

        Then we run 'vgscan --mknodes' to ensure that any /dev
        nodes have been created for the new LV.

        :param list lvcreate_args: list of lvcreate arguments.
        """
        log.debug(
            '--> running "lvcreate -Zn %s"', " ".join(lvcreate_args)
        )
        Command.run(
            ['lvcreate'] + lvm_tool_options + ['-Zn'] + lvcreate_args
        )
        log.debug(
            '--> running "vgscan --mknodes" to create missing nodes'
        )
        Command.run(
            ['vgscan'] + lvm_tool_options + ['--mknodes']
        )

    def create_volumes(self, filesystem_name):
        """
        Create configured lvm volumes and filesystems

        All volumes receive the same filesystem

        :param str filesystem_name: volumes filesystem name
        """
        log.info(
            'Creating volumes(%s)', filesystem_name
        )
        self.create_volume_paths_in_root_dir()

        canonical_volume_list = self.get_canonical_volume_list()
        for volume in canonical_volume_list.volumes:
            volume_mbsize = self.get_volume_mbsize(
                volume, self.volumes, filesystem_name,
                self.custom_args['resize_on_boot']
            )
            log.info(
                '--> volume %s with %s MB', volume.name, volume_mbsize
            )
            self._create_volume_no_zero(
                self.lvm_tool_options, [
                    '-L', format(volume_mbsize), '-n',
                    volume.name, self.volume_group
                ]
            )
            self.apply_attributes_on_volume(
                self.root_dir, volume
            )
            self._add_to_volume_map(volume.name)
            if volume.label != 'SWAP':
                self._create_filesystem(
                    volume.name, volume.label, filesystem_name
                )
                self._add_to_mount_list(
                    volume.name, volume.realpath
                )

        if canonical_volume_list.full_size_volume:
            full_size_volume = canonical_volume_list.full_size_volume
            log.info('--> fullsize volume %s', full_size_volume.name)
            self._create_volume_no_zero(
                self.lvm_tool_options, [
                    '-l', '+100%FREE', '-n',
                    full_size_volume.name, self.volume_group
                ]
            )
            self._add_to_volume_map(full_size_volume.name)
            self._create_filesystem(
                full_size_volume.name, full_size_volume.label, filesystem_name
            )
            self._add_to_mount_list(
                full_size_volume.name, full_size_volume.realpath
            )

        # re-order mount_list by mountpoint hierarchy
        # This is needed because the handling of the fullsize volume and
        # all other volumes is outside of the canonical order. If the
        # fullsize volume forms a nested structure together with another
        # volume the volume mount list must be re-ordered to avoid
        # mounting the volumes in the wrong order
        volume_paths = {}
        for volume_mount in self.mount_list:
            volume_paths[volume_mount.mountpoint] = volume_mount
        self.mount_list = []
        for mount_path in Path.sort_by_hierarchy(sorted(volume_paths.keys())):
            self.mount_list.append(volume_paths[mount_path])

    def get_fstab(
        self, persistency_type: str = 'by-label', filesystem_name: str = ''
    ) -> List[str]:
        """
        Implements creation of the fstab entries. The method
        returns a list of fstab compatible entries

        :param str persistency_type: unused
        :param str filesystem_name: volumes filesystem name

        :return: fstab entries

        :rtype: list
        """
        fstab_entries = []
        for volume_mount in self.mount_list:
            volume_name = self._get_volume_name_from_volume_map(
                volume_mount.device
            )
            if not self._is_root_volume(volume_name):
                path_start_index = len(defaults.TEMP_DIR.split(os.sep)) + 1
                mount_path = os.sep.join(
                    volume_mount.mountpoint.split(os.sep)[path_start_index:]
                )
                fs_check = self._is_volume_enabled_for_fs_check(volume_name)
                if not mount_path.startswith(os.sep):
                    mount_path = os.sep + mount_path
                fstab_entry = ' '.join(
                    [
                        volume_mount.device, mount_path, filesystem_name,
                        self.mount_options,
                        '0 {fs_passno}'.format(
                            fs_passno='2' if fs_check else '0'
                        )
                    ]
                )
                fstab_entries.append(fstab_entry)

        return fstab_entries

    def get_volumes(self) -> Dict:
        """
        Return dict of volumes

        :return: volumes dictionary

        :rtype: dict
        """
        volumes = {}
        path_start_index = len(defaults.TEMP_DIR.split(os.sep)) + 1
        for volume_mount in self.mount_list:
            mount_path = os.sep.join(
                volume_mount.mountpoint.split(os.sep)[path_start_index:]
            )
            if mount_path:
                volumes[mount_path] = {
                    'volume_options': self.mount_options,
                    'volume_device': volume_mount.device
                }
        return volumes

    def mount_volumes(self):
        """
        Mount lvm volumes
        """
        for volume_mount in self.mount_list:
            Path.create(volume_mount.mountpoint)
            volume_mount.mount(
                options=[self.mount_options]
            )

    def umount_volumes(self):
        """
        Umount lvm volumes
        """
        for volume_mount in reversed(self.mount_list):
            if volume_mount.is_mounted():
                volume_mount.umount()

    def _is_volume_enabled_for_fs_check(self, volume_name):
        for volume in self.volumes:
            if volume_name == volume.name:
                if 'enable-for-filesystem-check' in volume.attributes:
                    return True
        return False

    def _create_filesystem(self, volume_name, volume_label, filesystem_name):
        device_node = self.volume_map[volume_name]
        if self._is_root_volume(volume_name) and not volume_label:
            # if there is no @root volume definition for the root volume,
            # perform a second lookup of a label specified via the
            # rootfs_label from the type setup
            volume_label = self.custom_args['root_label']
        with FileSystem.new(
            name=filesystem_name,
            device_provider=MappedDevice(
                device=device_node, device_provider=self.device_provider_root
            ),
            custom_args=self.custom_filesystem_args
        ) as filesystem:
            filesystem.create_on_device(
                label=volume_label
            )

    def _add_to_mount_list(self, volume_name, realpath):
        device_node = self.volume_map[volume_name]
        if self._is_root_volume(volume_name):
            # root volume must be first in the list
            self.mount_list.insert(
                0, MountManager(
                    device=device_node,
                    mountpoint=self.mountpoint
                )
            )
        else:
            self.mount_list.append(
                MountManager(
                    device=device_node,
                    mountpoint=self.mountpoint + '/' + realpath
                )
            )

    def _add_to_volume_map(self, volume_name):
        self.volume_map[volume_name] = ''.join(
            ['/dev/', self.volume_group, '/', volume_name]
        )

    def _get_volume_name_from_volume_map(self, device):
        for volume_name, volume_path in self.volume_map.items():
            if volume_path == device:
                return volume_name

    def _volume_group_in_use_on_host_system(self, volume_group_name):
        vgs_call = Command.run(
            [
                'vgs', '--noheadings',
                '--select', 'vg_name={0}'.format(volume_group_name)
            ]
        )
        if vgs_call.output:
            # if vgs returned some information on the selected volume
            # group name, this indicates the group is in use
            return True
        else:
            # if vgs returned no information on the selected volume
            # group name, it is considered to be not used
            return False

    def _is_root_volume(self, volume_name):
        for volume in self.volumes:
            if volume_name == volume.name and volume.is_root_volume:
                return True

    def _is_swap_volume(self, volume_name):
        for volume in self.volumes:
            if volume_name == volume.name and volume.label == 'SWAP':
                return True

    def __exit__(self, exc_type, exc_value, traceback):
        if self.volume_group:
            try:
                self.umount_volumes()
                Command.run(
                    ['vgchange'] + self.lvm_tool_options + [
                        '-an', self.volume_group
                    ]
                )
            except KiwiCommandError as issue:
                log.error(
                    'volume group {0} detach failed with {1}'.format(
                        self.volume_group, issue
                    )
                )
