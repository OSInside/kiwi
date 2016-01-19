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
import time
import re

# project
from command import Command
from volume_manager_base import VolumeManagerBase
from mapped_device import MappedDevice
from filesystem import FileSystem
from data_sync import DataSync
from path import Path
from logger import log

from exceptions import (
    KiwiVolumeRootIDError
)


class VolumeManagerBtrfs(VolumeManagerBase):
    """
        Implements btrfs sub-volume management
    """
    def post_init(self, custom_args):
        if custom_args:
            self.custom_args = custom_args
        else:
            self.custom_args = {}
        if 'root_label' not in self.custom_args:
            self.custom_args['root_label'] = 'ROOT'

    def setup(self, name=None):
        filesystem = FileSystem(
            'btrfs', MappedDevice(device=self.device, device_provider=self)
        )
        filesystem.create_on_device(
            label=self.custom_args['root_label']
        )
        self.setup_mountpoint()
        Command.run(
            ['mount', self.device, self.mountpoint]
        )
        root_volume = self.mountpoint + '/@'
        Command.run(
            ['btrfs', 'subvolume', 'create', root_volume]
        )
        subvolume_list_call = Command.run(
            ['btrfs', 'subvolume', 'list', self.mountpoint]
        )
        id_search = re.search('ID (\d+) ', subvolume_list_call.output)
        if id_search:
            root_volume_id = id_search.group(1)
            Command.run(
                [
                    'btrfs', 'subvolume', 'set-default',
                    root_volume_id, self.mountpoint
                ]
            )
        else:
            raise KiwiVolumeRootIDError(
                'Failed to detect btrfs root volume ID'
            )

    def create_volumes(self, filesystem_name):
        log.info(
            'Creating %s sub volumes', filesystem_name
        )
        self.create_volume_paths_in_root_dir()

        canonical_volume_list = self.get_canonical_volume_list()
        if canonical_volume_list.full_size_volume:
            # put an eventual fullsize volume to the volume list
            # because there is no extra handling required for it on btrfs
            canonical_volume_list.volumes.append(
                canonical_volume_list.full_size_volume
            )

        for volume in canonical_volume_list.volumes:
            if volume.name == 'LVRoot':
                # the btrfs root volume named '@' has been created as
                # part of the setup procedure
                pass
            else:
                log.info('--> sub volume %s', volume.realpath)
                volume_path = self.mountpoint + '/@/'
                for subvol_element in volume.realpath.split('/'):
                    if subvol_element:
                        volume_path = volume_path + subvol_element + '/'
                        Command.run(
                            ['btrfs', 'subvolume', 'create', volume_path]
                        )

    def mount_volumes(self):
        # btrfs subvolumes doesn't need to be extra mounted
        pass

    def sync_data(self, exclude=None):
        if self.mountpoint and self.is_mounted():
            data = DataSync(self.root_dir, self.mountpoint + '/@')
            data.sync_data(exclude)

    def __del__(self):
        if self.is_mounted():
            log.info('Cleaning up %s instance', type(self).__name__)
            umounted_successfully = False
            for busy in [1, 2, 3]:
                try:
                    Command.run(['umount', self.device])
                    umounted_successfully = True
                    break
                except Exception:
                    log.warning(
                        '%d umount of %s failed, try again in 1sec',
                        busy, self.device
                    )
                    time.sleep(1)
            if umounted_successfully:
                Path.wipe(self.mountpoint)
            else:
                log.warning(
                    'mount path %s still busy', self.mountpoint
                )
