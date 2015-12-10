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
from collections import namedtuple
import time

# project
from command import Command
from volume_manager_base import VolumeManagerBase
from mapped_device import MappedDevice
from filesystem import FileSystem
from path import Path
from logger import log

from exceptions import (
    KiwiVolumeGroupConflict
)


class VolumeManagerLVM(VolumeManagerBase):
    """
        Implements LVM volume management
    """
    def post_init(self, custom_args):
        if custom_args:
            self.custom_args = custom_args
        else:
            self.custom_args = {}
        if 'root_label' not in self.custom_args:
            self.custom_args['root_label'] = 'ROOT'

    def get_device(self):
        """
            return names of volume devices, note that the mapping
            requires an explicit create_volumes() call
        """
        device_map = {}
        for volume_name, volume_node in self.volume_map.iteritems():
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
        if self.__volume_group_in_use_on_host_system(volume_group_name):
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
        log.info(
            'Creating volumes(%s)', filesystem_name
        )
        self.create_volume_paths_in_source_dir()

        canonical_volume_list = self.get_canonical_volume_list()
        for volume in canonical_volume_list.volumes:
            [size_type, volume_mbsize] = volume.size.split(':')
            volume_mbsize = self.get_volume_mbsize(
                volume_mbsize, size_type, volume.realpath, filesystem_name
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
            self.__add_to_volume_map(volume.name)
            self.__create_filesystem(
                volume.name, filesystem_name
            )
            self.__add_to_mount_list(
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
            self.__add_to_volume_map(full_size_volume.name)
            self.__create_filesystem(
                full_size_volume.name, filesystem_name
            )
            self.__add_to_mount_list(
                full_size_volume.name, full_size_volume.realpath
            )

    def mount_volumes(self):
        self.setup_mountpoint()
        for mount in self.mount_list:
            Path.create(self.mountpoint + mount.mountpoint)
            Command.run(
                ['mount', mount.device, self.mountpoint + mount.mountpoint]
            )

    def __create_filesystem(self, volume_name, filesystem_name):
        device_node = self.volume_map[volume_name]
        label = None
        if volume_name == 'LVRoot':
            label = self.custom_args['root_label']
        filesystem = FileSystem(
            filesystem_name,
            MappedDevice(device=device_node, device_provider=self)
        )
        filesystem.create_on_device(
            label=label
        )

    def __add_to_mount_list(self, volume_name, realpath):
        mount_type = namedtuple(
            'mount_type', [
                'device', 'mountpoint'
            ]
        )
        device_node = self.volume_map[volume_name]
        if volume_name == 'LVRoot':
            # root volume must be first in the list
            self.mount_list.insert(
                0, mount_type(
                    device=device_node,
                    mountpoint='/'
                )
            )
        else:
            self.mount_list.append(
                mount_type(
                    device=device_node,
                    mountpoint='/' + realpath
                )
            )

    def __add_to_volume_map(self, volume_name):
        self.volume_map[volume_name] = ''.join(
            ['/dev/', self.volume_group, '/', volume_name]
        )

    def __volume_group_in_use_on_host_system(self, volume_group_name):
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
            if self.is_mounted():
                all_volumes_umounted = True
                for mount in reversed(self.mount_list):
                    umounted_successfully = False
                    for busy in [1, 2, 3]:
                        try:
                            Command.run(['umount', mount.device])
                            umounted_successfully = True
                            break
                        except Exception:
                            log.warning(
                                '%d umount of %s failed, try again in 1sec',
                                busy, mount.device
                            )
                            time.sleep(1)
                    if not umounted_successfully:
                        all_volumes_umounted = False
                        log.warning(
                            '%s still busy at %s',
                            self.mountpoint + mount.mountpoint,
                            type(self).__name__
                        )
                if all_volumes_umounted:
                    Path.wipe(self.mountpoint)
            try:
                Command.run(['vgchange', '-an', self.volume_group])
            except Exception:
                log.warning(
                    'volume group %s still busy', self.volume_group
                )
