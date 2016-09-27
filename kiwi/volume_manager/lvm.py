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
# project
from .base import VolumeManagerBase
from ..command import Command
from ..mount_manager import MountManager
from ..storage.mapped_device import MappedDevice
from ..filesystem import FileSystem
from ..path import Path
from ..logger import log

from ..exceptions import (
    KiwiVolumeGroupConflict
)


class VolumeManagerLVM(VolumeManagerBase):
    """
    Implements LVM volume management
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
        if 'image_type' not in self.custom_args:
            self.custom_args['image_type'] = None

        if self.custom_filesystem_args['mount_options']:
            self.mount_options = self.custom_filesystem_args['mount_options'][0]
        else:
            self.mount_options = 'defaults'

    def get_device(self):
        """
        Dictionary of MappedDevice instances per volume

        Note: The mapping requires an explicit create_volumes() call

        :return: root plus volume device map
        :rtype: dict
        """
        device_map = {}
        for volume_name, volume_node in list(self.volume_map.items()):
            if volume_name == 'LVRoot':
                # LVRoot volume device takes precedence over the
                # root partition device from the disk. Therefore use
                # the same key to put them on the same level
                volume_name = 'root'
            device_map[volume_name] = MappedDevice(
                device=volume_node, device_provider=self
            )
        return device_map

    def setup(self, volume_group_name='systemVG'):
        """
        Setup lvm volume management

        In case of LVM a new volume group is created on a PV
        initialized storage device

        :param string name: volume group name
        """
        self.setup_mountpoint()

        if self._volume_group_in_use_on_host_system(volume_group_name):
            raise KiwiVolumeGroupConflict(
                'Requested volume group %s is in use on this host' %
                volume_group_name
            )
        log.info(
            'Creating volume group %s', volume_group_name
        )
        Command.run(
            command=['vgremove', '--force', volume_group_name],
            raise_on_error=False
        )
        Command.run(['pvcreate', self.device])
        Command.run(['vgcreate', volume_group_name, self.device])
        self.volume_group = volume_group_name

    def create_volumes(self, filesystem_name):
        """
        Create configured lvm volumes and filesystems

        All volumes receive the same filesystem

        :param string filesystem_name: volumes filesystem name
        """
        log.info(
            'Creating volumes(%s)', filesystem_name
        )
        self.create_volume_paths_in_root_dir()

        canonical_volume_list = self.get_canonical_volume_list()
        for volume in canonical_volume_list.volumes:
            [size_type, volume_mbsize] = volume.size.split(':')
            volume_mbsize = self.get_volume_mbsize(
                volume_mbsize,
                size_type,
                volume.realpath,
                filesystem_name,
                self.custom_args['image_type']
            )
            log.info(
                '--> volume %s with %s MB', volume.name, volume_mbsize
            )
            Command.run(
                [
                    'lvcreate', '-L', format(volume_mbsize), '-n',
                    volume.name, self.volume_group
                ]
            )
            self._add_to_volume_map(volume.name)
            self._create_filesystem(
                volume.name, filesystem_name
            )
            self._add_to_mount_list(
                volume.name, volume.realpath
            )

        if canonical_volume_list.full_size_volume:
            full_size_volume = canonical_volume_list.full_size_volume
            log.info('--> fullsize volume %s', full_size_volume.name)
            Command.run(
                [
                    'lvcreate', '-l', '+100%FREE', '-n', full_size_volume.name,
                    self.volume_group
                ]
            )
            self._add_to_volume_map(full_size_volume.name)
            self._create_filesystem(
                full_size_volume.name, filesystem_name
            )
            self._add_to_mount_list(
                full_size_volume.name, full_size_volume.realpath
            )

    def get_fstab(self, persistency_type, filesystem_name):
        """
        Implements creation of the fstab entries. The method
        returns a list of fstab compatible entries

        :param string persistency_type: unused
        :param string filesystem_name: volumes filesystem name

        :rtype: list
        """
        fstab_entries = []
        for volume_mount in self.mount_list:
            if 'LVRoot' not in volume_mount.device:
                mount_path = '/'.join(volume_mount.mountpoint.split('/')[3:])
                if not mount_path.startswith('/'):
                    mount_path = '/' + mount_path
                fstab_entry = ' '.join(
                    [
                        volume_mount.device, mount_path, filesystem_name,
                        self.mount_options, '1 2'
                    ]
                )
                fstab_entries.append(fstab_entry)

        return fstab_entries

    def get_volumes(self):
        """
        Return dict of volumes

        :rtype: dict
        """
        volumes = {}
        for volume_mount in self.mount_list:
            mount_path = '/'.join(volume_mount.mountpoint.split('/')[3:])
            volumes[mount_path] = self.mount_options
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
        all_volumes_umounted = True
        for volume_mount in reversed(self.mount_list):
            if volume_mount.is_mounted():
                if not volume_mount.umount():
                    all_volumes_umounted = False
        return all_volumes_umounted

    def _create_filesystem(self, volume_name, filesystem_name):
        device_node = self.volume_map[volume_name]
        label = None
        if volume_name == 'LVRoot':
            label = self.custom_args['root_label']
        filesystem = FileSystem(
            name=filesystem_name,
            device_provider=MappedDevice(
                device=device_node, device_provider=self
            ),
            custom_args=self.custom_filesystem_args
        )
        filesystem.create_on_device(
            label=label
        )

    def _add_to_mount_list(self, volume_name, realpath):
        device_node = self.volume_map[volume_name]
        if volume_name == 'LVRoot':
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

    def _volume_group_in_use_on_host_system(self, volume_group_name):
        vgs_call = Command.run(
            ['vgs', '--noheadings', '-o', 'vg_name']
        )
        for host_volume_group_name in vgs_call.output.split('\n'):
            if volume_group_name in host_volume_group_name:
                return True
        return False

    def __del__(self):
        if self.volume_group:
            log.info('Cleaning up %s instance', type(self).__name__)
            if self.umount_volumes():
                Path.wipe(self.mountpoint)
                try:
                    Command.run(['vgchange', '-an', self.volume_group])
                except Exception:
                    log.warning(
                        'volume group %s still busy', self.volume_group
                    )
