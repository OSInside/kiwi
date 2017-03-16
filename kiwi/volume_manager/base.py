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
import os

# project
from kiwi.logger import log
from kiwi.command import Command
from kiwi.storage.device_provider import DeviceProvider
from kiwi.mount_manager import MountManager
from kiwi.storage.mapped_device import MappedDevice
from kiwi.utils.sync import DataSync
from kiwi.path import Path
from kiwi.system.size import SystemSize
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiVolumeManagerSetupError
)


class VolumeManagerBase(DeviceProvider):
    """
    Implements base class for volume management interface

    Attributes

    * :attr:`mountpoint`
        root mountpoint for volumes

    * :attr:`device_provider`
        Instance of class based on DeviceProvider

    * :attr:`root_dir`
        root directory path name

    * :attr:`volumes`
        list of volumes from XMLState::get_volumes()

    * :attr:`volume_group`
        volume group name

    * :attr:`volume_map`
        map volume name to device node

    * :attr:`mount_list`
        list of volume MountManager's

    * :attr:`device`
        storage device node name

    * :attr:`custom_args`
        custom volume manager arguments for all volume manager
        and filesystem specific tasks

    * :attr:`custom_filesystem_args`
        custom filesystem creation and mount arguments, subset
        of the custom_args information suitable to be passed
        to a FileSystem instance
    """
    def __init__(self, device_provider, root_dir, volumes, custom_args=None):
        # all volumes are combined into one mountpoint. This is
        # needed at sync_data time. How to mount the volumes is
        # special to the volume management class
        self.mountpoint = None

        # bind the device providing class instance to this object.
        # This is done to guarantee the correct destructor order when
        # the device should be released.
        self.device_provider = device_provider

        # An indicator for the mount of the filesystem and its volumes
        # when mounted for the first time
        self.volumes_mounted_initially = False

        self.root_dir = root_dir
        self.volumes = volumes
        self.volume_group = None
        self.volume_map = {}
        self.mount_list = []

        self.device = self.device_provider.get_device()

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

        :param string name: unused
        """
        raise NotImplementedError

    def create_volumes(self, filesystem_name):
        """
        Implements creation of volumes

        Implementation in specialized volume manager class required

        :param string filesystem_name: unused
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

        :param string persistency_type: unused
        :param string filesystem_name: unused

        :rtype: list
        """
        raise NotImplementedError

    def get_volumes(self):
        """
        Implements return of dictionary of volumes and
        their mount options

        :rtype: dict
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

        :rtype: bool
        """
        return self.device_provider.is_loop()

    def get_device(self):
        """
        Dictionary with instance of MappedDevice for the root device node

        :return: root device map
        :rtype: dict
        """
        return {
            'root': MappedDevice(
                device=self.device, device_provider=self
            )
        }

    def create_volume_paths_in_root_dir(self):
        """
        Implements creation of volume paths in the given root directory
        """
        for volume in self.volumes:
            if volume.realpath and not volume.realpath == '/':
                volume_image_path = os.path.normpath(
                    self.root_dir + '/' + volume.realpath
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
        self, mbsize, size_type, realpath, filesystem_name, image_type=None
    ):
        """
        Implements size lookup for the given path and desired
        filesystem according to the specified size type

        :param int mbsize: configured volume size
        :param string size_type: relative or absolute size setup
        :param string realpath: volume real path name
        :param string filesystem_name: filesystem name
        :param image_type: build type name

        :return: mbsize
        :rtype: int
        """
        if image_type and image_type == 'oem':
            # only for vmx types we need to create the volumes in the
            # configured size. oem disks are self expandable and will
            # resize to the configured sizes on first boot of the disk
            # image. Therefore the requested size is set to null
            # and we add the required minimum size to hold the data
            size_type = 'freespace'
            mbsize = 0

        if size_type == 'freespace':
            # Please note for nested volumes which contains other volumes
            # the freespace calculation is not correct. Example:
            # /usr is a volume and /usr/lib is a volume. If freespace is
            # set for the /usr volume the data size calculated also
            # contains the data of the /usr/lib path which will live in
            # an extra volume later. The result will be more freespace
            # than expected ! Especially for the root volume this matters
            # most because it always nests all other volumes. Thus it is
            # better to use a fixed size for the root volume if it is not
            # configured to use all rest space
            #
            # You are invited to fix it :)
            volume_size = SystemSize(
                self.root_dir + '/' + realpath
            )
            mbsize = int(mbsize) + \
                Defaults.get_min_volume_mbytes()
            mbsize += volume_size.customize(
                volume_size.accumulate_mbyte_file_sizes(),
                filesystem_name
            )
        return mbsize

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
                options=['-a', '-H', '-X', '-A', '--one-file-system'],
                exclude=exclude
            )
            self.umount_volumes()

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

    def __del__(self):
        """
        Implements destructor to cleanup all volume subsystems
        and mount processes. overwrite in specialized volume
        management class
        """
        pass
