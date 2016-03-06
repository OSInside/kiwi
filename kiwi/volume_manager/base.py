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
from ..storage.device_provider import DeviceProvider
from ..mount_manager import MountManager
from ..data_sync import DataSync
from ..path import Path
from ..system_size import SystemSize
from ..defaults import Defaults

from ..exceptions import (
    KiwiVolumeManagerSetupError
)


class VolumeManagerBase(DeviceProvider):
    """
        Implements base class for volume management interface
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

        self.post_init(custom_args)

    def setup(self, name=None):
        """
            Implements setup required prior to the creation
            of storage volumes
        """
        raise NotImplementedError

    def create_volumes(self, filesystem_name):
        """
            Implements creation of storage volumes
        """
        raise NotImplementedError

    def mount_volumes(self):
        """
            Implements mounting of all volumes below one
            master directory
        """
        raise NotImplementedError

    def umount_volumes(self):
        """
            Implements umounting of all volumes
        """
        raise NotImplementedError

    def post_init(self, custom_args):
        """
            Called after init to handle e.g custom arguments
        """
        pass

    def is_loop(self):
        """
            Is this device provider loop based
        """
        return self.device_provider.is_loop()

    def get_device(self):
        """
            Return device map for this device provider
            overwrite if specialized volume management creates
            new devices like it is the case for e.g LVM
        """
        return self.device_provider.get_device()

    def create_volume_paths_in_root_dir(self):
        """
            Implements creation of volume paths in the given
            root directory
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
        """
        if self.mountpoint:
            root_mount = MountManager(device=None, mountpoint=self.mountpoint)
            if not root_mount.is_mounted():
                self.mount_volumes()
            data = DataSync(self.root_dir, self.mountpoint)
            data.sync_data(exclude)
            self.umount_volumes()

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
