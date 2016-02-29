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
from tempfile import mkdtemp

# project
from ..logger import log
from ..data_sync import DataSync
from ..mount_manager import MountManager

from ..exceptions import (
    KiwiFileSystemSyncError
)


class FileSystemBase(object):
    """
        Implements base class for filesystem interface
    """
    def __init__(self, device_provider, root_dir=None, custom_args=None):
        # filesystems created with a block device stores the mountpoint
        # here. The file name of the file containing the filesystem is
        # stored in the device_provider if the filesystem is represented
        # as a file there
        self.filesystem_mount = None

        # bind the block device providing class instance to this object.
        # This is done to guarantee the correct destructor order when
        # the device should be released. This is only required if the
        # filesystem required a block device to become created
        self.device_provider = device_provider

        self.root_dir = root_dir

        # filesystems created without a block device stores the result
        # filesystem file name here
        self.filename = None

        self.custom_args = []
        self.post_init(custom_args)

    def post_init(self, custom_args):
        # overwrite in specialized filesystem class when needed
        pass

    def create_on_device(self, label=None):
        # implement for filesystems which requires a block device to
        # become created, e.g ext4.
        raise NotImplementedError

    def create_on_file(self, filename, label=None):
        # implement for filesystems which doesn't need a block device
        # to become created, e.g squashfs
        raise NotImplementedError

    def sync_data(self, exclude=None):
        if not self.root_dir:
            raise KiwiFileSystemSyncError(
                'no root directory specified'
            )
        if not os.path.exists(self.root_dir):
            raise KiwiFileSystemSyncError(
                'given root directory %s does not exist' % self.root_dir
            )
        self.filesystem_mount = MountManager(
            device=self.device_provider.get_device(),
            mountpoint=mkdtemp(prefix='kiwi_filesystem.')
        )
        self.filesystem_mount.mount()
        data = DataSync(
            self.root_dir, self.filesystem_mount.mountpoint
        )
        data.sync_data(exclude)
        self.filesystem_mount.umount()

    def __del__(self):
        if self.filesystem_mount:
            log.info('Cleaning up %s instance', type(self).__name__)
            self.filesystem_mount.umount()
