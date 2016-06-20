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
import re
import os

# project
from ..command import Command
from .base import VolumeManagerBase
from ..mount_manager import MountManager
from ..storage.mapped_device import MappedDevice
from ..filesystem import FileSystem
from ..utils.sync import DataSync
from ..path import Path
from ..logger import log

from ..exceptions import (
    KiwiVolumeRootIDError
)


class VolumeManagerBtrfs(VolumeManagerBase):
    """
    Implements btrfs sub-volume management
    """
    def post_init(self, custom_args):
        """
        Post initialization method

        Store custom btrfs initialization arguments

        Attributes

        * :attr:`subvol_mount_list`
            list of mounted btrfs subvolumes

        * :attr:`toplevel_mount`
            MountManager for root mountpoint

        :param list custom_args: custom btrfs volume manager arguments
        """
        if custom_args:
            self.custom_args = custom_args
        else:
            self.custom_args = {}
        if 'root_label' not in self.custom_args:
            self.custom_args['root_label'] = 'ROOT'
        if 'root_is_snapshot' not in self.custom_args:
            self.custom_args['root_is_snapshot'] = False

        self.subvol_mount_list = []
        self.toplevel_mount = None

    def setup(self, name=None):
        """
        Setup btrfs volume management

        In case of btrfs a toplevel(@) subvolume is created and marked
        as default volume. If snapshots are activated via the custom_args
        the setup method also created the @/.snapshots/1/snapshot
        subvolumes. There is no concept of a volume manager name, thus
        the name argument is not used for btrfs

        :param string name: unused
        """
        self.setup_mountpoint()

        filesystem = FileSystem(
            name='btrfs',
            device_provider=MappedDevice(
                device=self.device, device_provider=self
            ),
            custom_args=self.custom_filesystem_args
        )
        filesystem.create_on_device(
            label=self.custom_args['root_label']
        )
        self.toplevel_mount = MountManager(
            device=self.device, mountpoint=self.mountpoint
        )
        self.toplevel_mount.mount(
            self.custom_filesystem_args['mount_options']
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
            self._set_default_volume('@/.snapshots/1/snapshot')
        else:
            self._set_default_volume('@')

    def create_volumes(self, filesystem_name):
        """
        Create configured btrfs subvolumes

        Any btrfs subvolume is of the same btrfs filesystem. There is no
        way to have different filesystems per btrfs subvolume. Thus
        the filesystem_name has no effect for btrfs

        :param string filesystem_name: unused
        """
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
                    [
                        'btrfs', 'subvolume', 'create',
                        os.path.normpath(toplevel + volume.realpath)
                    ]
                )
                if self.custom_args['root_is_snapshot']:
                    snapshot = self.mountpoint + '/@/.snapshots/1/snapshot/'
                    volume_mount = MountManager(
                        device=self.device,
                        mountpoint=os.path.normpath(snapshot + volume.realpath)
                    )
                    self.subvol_mount_list.append(
                        volume_mount
                    )

    def mount_volumes(self):
        """
        Mount btrfs subvolumes
        """
        for volume_mount in self.subvol_mount_list:
            if not os.path.exists(volume_mount.mountpoint):
                Path.create(volume_mount.mountpoint)
            subvol_name = os.path.basename(volume_mount.mountpoint)
            subvol_options = ','.join(
                [
                    'subvol=' + os.path.normpath('@/' + subvol_name)
                ] + self.custom_filesystem_args['mount_options']
            )
            volume_mount.mount(
                options=[subvol_options]
            )

    def umount_volumes(self):
        """
        Umount btrfs subvolumes
        """
        all_volumes_umounted = True
        for volume_mount in reversed(self.subvol_mount_list):
            if volume_mount.is_mounted():
                if not volume_mount.umount():
                    all_volumes_umounted = False

        if all_volumes_umounted:
            if self.toplevel_mount.is_mounted():
                if not self.toplevel_mount.umount():
                    all_volumes_umounted = False

        return all_volumes_umounted

    def sync_data(self, exclude=None):
        """
        Sync data into btrfs filesystem

        If snapshots are activated the root filesystem is synced
        into the first snapshot
        """
        if self.toplevel_mount:
            sync_target = self.mountpoint + '/@'
            if self.custom_args['root_is_snapshot']:
                sync_target = self.mountpoint + '/@/.snapshots/1/snapshot'
            data = DataSync(self.root_dir, sync_target)
            data.sync_data(
                options=['-a', '-H', '-X', '-A', '--one-file-system'],
                exclude=exclude
            )

    def _set_default_volume(self, default_volume):
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

    def __del__(self):
        if self.toplevel_mount:
            log.info('Cleaning up %s instance', type(self).__name__)
            if self.umount_volumes():
                Path.wipe(self.mountpoint)
