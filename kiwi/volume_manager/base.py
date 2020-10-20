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
from tempfile import mkdtemp
import logging
import os

# project
from kiwi.command import Command
from kiwi.storage.device_provider import DeviceProvider
from kiwi.mount_manager import MountManager
from kiwi.utils.sync import DataSync
from kiwi.path import Path
from kiwi.system.size import SystemSize
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiVolumeManagerSetupError
)

log = logging.getLogger('kiwi')


class VolumeManagerBase(DeviceProvider):
    """
    **Implements base class for volume management interface**

    :param str mountpoint: root mountpoint for volumes
    :param object device_map:
        dictionary of low level DeviceProvider intances
    :param str root_dir: root directory path name
    :param list volumes: list of volumes from :class:`XMLState::get_volumes()`
    :param str volume_group: volume group name
    :param map volume_map: map volume name to device node
    :param list mount_list: list of volume MountManager's
    :param str device: storage device node name
    :param dict custom_args: custom volume manager arguments for all
        volume manager and filesystem specific tasks
    :param list custom_filesystem_args: custom filesystem creation and mount
        arguments, subset of the custom_args information suitable to
        be passed to a FileSystem instance

    :raises KiwiVolumeManagerSetupError: if the given root_dir doesn't exist
    """
    def __init__(self, device_map, root_dir, volumes, custom_args=None):
        self.temp_directories = []
        # all volumes are combined into one mountpoint. This is
        # needed at sync_data time. How to mount the volumes is
        # special to the volume management class
        self.mountpoint = None

        # dictionary of mapped DeviceProviders
        self.device_map = device_map

        # bind the device providing class instance to this object.
        # This is done to guarantee the correct destructor order when
        # the device should be released.
        self.device_provider_root = device_map['root']

        # An indicator for the mount of the filesystem and its volumes
        # when mounted for the first time
        self.volumes_mounted_initially = False

        self.root_dir = root_dir
        self.volumes = volumes
        self.volume_group = None
        self.volume_map = {}
        self.mount_list = []

        # Main device to operate on
        self.device = self.device_provider_root.get_device()

        if not os.path.exists(root_dir):
            raise KiwiVolumeManagerSetupError(
                'given root directory %s does not exist' % root_dir
            )

        self.custom_args = {}
        self.custom_filesystem_args = {
            'create_options': [],
            'mount_options': []
        }

        if custom_args and 'fs_create_options' in custom_args:
            self.custom_filesystem_args['create_options'] = \
                custom_args['fs_create_options']

        if custom_args and 'fs_mount_options' in custom_args:
            self.custom_filesystem_args['mount_options'] = \
                custom_args['fs_mount_options']

        if custom_args and 'fs_create_options' in custom_args:
            self.custom_filesystem_args['create_options'] = \
                custom_args['fs_create_options']

        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Implementation in specialized volume manager class if required

        :param dict custom_args: unused
        """
        pass

    def setup(self, name=None):
        """
        Implements setup required prior to the creation of volumes

        Implementation in specialized volume manager class required

        :param str name: unused
        """
        raise NotImplementedError

    def create_volumes(self, filesystem_name):
        """
        Implements creation of volumes

        Implementation in specialized volume manager class required

        :param str filesystem_name: unused
        """
        raise NotImplementedError

    def apply_attributes_on_volume(self, toplevel, volume):
        for attribute in volume.attributes:
            if attribute == 'no-copy-on-write':
                log.info(
                    '--> setting {0} for {1}'.format(attribute, volume.realpath)
                )
                Command.run(
                    [
                        'chattr', '+C',
                        os.path.normpath(toplevel + volume.realpath)
                    ]
                )

    def get_fstab(self, persistency_type, filesystem_name):
        """
        Implements setup of the fstab entries. The method should
        return a list of fstab compatible entries

        :param str persistency_type: unused
        :param str filesystem_name: unused
        """
        raise NotImplementedError

    def get_volumes(self):
        """
        Implements return of dictionary of volumes and
        their mount options
        """
        raise NotImplementedError

    def mount_volumes(self):
        """
        Implements mounting of all volumes below one master directory

        Implementation in specialized volume manager class required
        """
        raise NotImplementedError

    def umount_volumes(self):
        """
        Implements umounting of all volumes

        Implementation in specialized volume manager class required
        """
        raise NotImplementedError

    def is_loop(self):
        """
        Check if storage provider is loop based

        The information is taken from the storage provider. If
        the storage provider is loop based the volume manager is it too

        :return: True of False

        :rtype: bool
        """
        return self.device_provider_root.is_loop()

    def get_device(self):
        """
        Return current DeviceProvider dictionary

        :return: device_map

        :rtype: dict
        """
        return self.device_map

    def create_volume_paths_in_root_dir(self):
        """
        Implements creation of volume paths in the given root directory
        """
        for volume in self.volumes:
            if volume.realpath and volume.realpath not in ['/', 'swap']:
                volume_image_path = os.path.normpath(
                    self.root_dir + os.sep + volume.realpath
                )
                if not os.path.exists(volume_image_path):
                    # not existing volume paths will be created in the image
                    # root directory. This happens hidden to the user but is
                    # imho ok because the path is explicitly configured as a
                    # volume
                    Path.create(volume_image_path)

    def get_canonical_volume_list(self):
        """
        Implements hierarchical sorting of volumes according to their
        paths and provides information about the volume configured as
        the one eating all the rest space

        :return: list of canonical_volume_type tuples

        :rtype: list
        """
        canonical_volume_type = namedtuple(
            'canonical_volume_type', [
                'volumes', 'full_size_volume'
            ]
        )
        volume_paths = {}
        full_size_volume = None
        for volume in self.volumes:
            if volume.fullsize:
                full_size_volume = volume
            elif volume.realpath:
                volume_paths[volume.realpath] = volume

        volume_list = []
        for realpath in Path.sort_by_hierarchy(sorted(volume_paths.keys())):
            volume_list.append(volume_paths[realpath])
        return canonical_volume_type(
            volumes=volume_list, full_size_volume=full_size_volume
        )

    def get_volume_mbsize(
        self, volume, all_volumes, filesystem_name, resize_on_boot=False
    ):
        """
        Implements size lookup for the given path and desired
        filesystem according to the specified size type

        :param tuple volume: volume to check size for
        :param list all_volumes: list of all volume tuples
        :param str filesystem_name: filesystem name
        :param resize_on_boot:
            specify the time of the resize. If the resize happens at
            boot time the volume size is only the minimum size to
            just store the data. If the volume size is fixed and
            does not change at boot time the returned size is the
            requested size which can be greater than the minimum
            needed size.

        :return: mbsize

        :rtype: int
        """
        [size_type, mbsize] = volume.size.split(':')
        lookup_path = volume.realpath
        lookup_abspath = os.path.normpath(
            os.sep.join([self.root_dir, lookup_path])
        )
        mbsize = int(mbsize)

        if resize_on_boot:
            # If resize_on_boot is true, the disk is self expandable and
            # will resize to the configured sizes on first boot
            # Therefore the requested size is set to null and we add
            # the required minimum size for just storing the data
            size_type = 'freespace'
            mbsize = Defaults.get_min_volume_mbytes()

        if size_type == 'freespace' and os.path.exists(lookup_abspath):
            exclude_paths = []
            for volume in all_volumes:
                volume_path = volume.realpath
                if lookup_path == volume_path:
                    continue
                if lookup_path == os.sep:
                    # exclude any sub volume path if lookup_path is /
                    exclude_paths.append(
                        os.path.normpath(self.root_dir + os.sep + volume_path)
                    )
                elif volume_path.startswith(lookup_path):
                    # exclude any sub volume path below lookup_path
                    exclude_paths.append(
                        os.path.normpath(self.root_dir + os.sep + volume_path)
                    )

            volume_size = SystemSize(lookup_abspath)
            if mbsize != Defaults.get_min_volume_mbytes():
                mbsize += Defaults.get_min_volume_mbytes()
            mbsize += volume_size.customize(
                volume_size.accumulate_mbyte_file_sizes(exclude_paths),
                filesystem_name
            )
        return mbsize

    def get_mountpoint(self):
        """
        Provides mount point directory

        Effective use of the directory is guaranteed only after sync_data

        :return: directory path name

        :rtype: string
        """
        return self.mountpoint

    def sync_data(self, exclude=None):
        """
        Implements sync of root directory to mounted volumes

        :param list exclude: file patterns to exclude
        """
        if self.mountpoint:
            root_mount = MountManager(device=None, mountpoint=self.mountpoint)
            if not root_mount.is_mounted():
                self.mount_volumes()
            data = DataSync(self.root_dir, self.mountpoint)
            data.sync_data(
                options=Defaults.get_sync_options(), exclude=exclude
            )

    def set_property_readonly_root(self):
        """
        Implements setup of read-only root property
        """
        raise KiwiVolumeManagerSetupError(
            'read only property not supported'
        )

    def setup_mountpoint(self):
        """
        Implements creation of a master directory holding
        the mounts of all volumes
        """
        self.mountpoint = mkdtemp(prefix='kiwi_volumes.')
        self.temp_directories.append(self.mountpoint)

    def _cleanup_tempdirs(self):
        for directory in self.temp_directories:
            Path.wipe(directory)
