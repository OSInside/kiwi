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
import os

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
        if 'root_is_snapshot' not in self.custom_args:
            self.custom_args['root_is_snapshot'] = False

        self.subvol_mount_list = []

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
        if self.custom_args['root_is_snapshot']:
            snapshot_volume = self.mountpoint + '/@/.snapshots'
            Command.run(
                ['btrfs', 'subvolume', 'create', snapshot_volume]
            )
            Path.create(snapshot_volume + '/1')
            snapshot = self.mountpoint + '/@/.snapshots/1/snapshot'
            Command.run(
                ['btrfs', 'subvolume', 'snapshot', root_volume, snapshot]
            )
            self.__set_default_volume('@/.snapshots/1/snapshot')
        else:
            self.__set_default_volume('@')

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
                toplevel = self.mountpoint + '/@/'
                volume_parent_path = os.path.normpath(
                    toplevel + os.path.dirname(volume.realpath)
                )
                if not os.path.exists(volume_parent_path):
                    Path.create(volume_parent_path)
                Command.run(
                    ['btrfs', 'subvolume', 'create', toplevel + volume.realpath]
                )
                self.subvol_mount_list.append(
                    volume.realpath
                )

    def mount_volumes(self):
        if self.custom_args['root_is_snapshot']:
            snapshot = self.mountpoint + '/@/.snapshots/1/snapshot/'
            for subvol in self.subvol_mount_list:
                volume_parent_path = os.path.normpath(
                    os.path.dirname(snapshot + subvol)
                )
                if not os.path.exists(volume_parent_path):
                    Path.create(volume_parent_path)
                Command.run(
                    [
                        'mount', self.device,
                        os.path.normpath(snapshot + subvol),
                        '-o subvol=' + os.path.normpath('@/' + subvol)
                    ]
                )

    def sync_data(self, exclude=None):
        if self.mountpoint and self.is_mounted():
            data = DataSync(self.root_dir, self.mountpoint + '/@')
            data.sync_data(exclude)

    def __set_default_volume(self, default_volume):
        subvolume_list_call = Command.run(
            ['btrfs', 'subvolume', 'list', self.mountpoint]
        )
        for subvolume in subvolume_list_call.output.split('\n'):
            id_search = re.search('ID (\d+) .*path (.*)', subvolume)
            if id_search:
                volume_id = id_search.group(1)
                volume_path = id_search.group(2)
                if volume_path == default_volume:
                    Command.run(
                        [
                            'btrfs', 'subvolume', 'set-default',
                            volume_id, self.mountpoint
                        ]
                    )
                    return

        raise KiwiVolumeRootIDError(
            'Failed to find btrfs volume: %s' % default_volume
        )

    def __try_umount(self, mount_point, wipe=True):
        umounted_successfully = False
        for busy in [1, 2, 3]:
            try:
                Command.run(['umount', os.path.normpath(mount_point)])
                umounted_successfully = True
                break
            except Exception:
                log.warning(
                    '%d umount of %s failed, try again in 1sec',
                    busy, mount_point
                )
                time.sleep(1)
        if umounted_successfully and wipe:
            Path.wipe(self.mountpoint)
        elif not umounted_successfully:
            log.warning(
                'mount path %s still busy', mount_point
            )

    def __del__(self):
        if self.is_mounted():
            log.info('Cleaning up %s instance', type(self).__name__)
            for subvol in reversed(self.subvol_mount_list):
                subvol_mount = \
                    self.mountpoint + '/@/.snapshots/1/snapshot/' + subvol
                self.__try_umount(mount_point=subvol_mount, wipe=False)

            self.__try_umount(mount_point=self.device)
