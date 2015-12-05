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
import time
from tempfile import mkdtemp

# project
from command import Command
from logger import log
from path import Path
from data_sync import DataSync

from exceptions import (
    KiwiFileSystemSyncError
)


class FileSystemBase(object):
    """
        Implements base class for filesystem interface
    """
    def __init__(self, device_provider, source_dir=None, custom_args=None):
        # filesystems created with a block device stores the mountpoint
        # here. The file name of the file containing the filesystem is
        # stored in the device_provider if the filesystem is represented
        # as a file there
        self.mountpoint = None

        # bind the block device providing class instance to this object.
        # This is done to guarantee the correct destructor order when
        # the device should be released. This is only required if the
        # filesystem required a block device to become created
        self.device_provider = device_provider

        self.source_dir = source_dir

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
        if not self.source_dir:
            raise KiwiFileSystemSyncError(
                'no source directory specified'
            )
        if not os.path.exists(self.source_dir):
            raise KiwiFileSystemSyncError(
                'given source directory %s does not exist' % self.source_dir
            )
        device = self.device_provider.get_device()
        Command.run(
            ['mount', device, self.__setup_mountpoint()]
        )
        if self.mountpoint and self.is_mounted():
            data = DataSync(self.source_dir, self.mountpoint)
            data.sync_data(exclude)
            Command.run(
                ['umount', self.mountpoint]
            )
            Path.remove(self.mountpoint)
            self.mountpoint = None

    def is_mounted(self):
        if self.mountpoint:
            try:
                Command.run(['mountpoint', self.mountpoint])
                return True
            except Exception:
                pass
        return False

    def __setup_mountpoint(self):
        self.mountpoint = mkdtemp(prefix='kiwi_filesystem.')
        return self.mountpoint

    def __del__(self):
        if self.mountpoint:
            log.info('Cleaning up %s instance', type(self).__name__)
            if self.is_mounted():
                umounted_successfully = False
                for busy in [1, 2, 3]:
                    try:
                        Command.run(['umount', self.mountpoint])
                        umounted_successfully = True
                        break
                    except Exception:
                        log.warning(
                            'umount of %s failed, try again in 1sec',
                            self.mountpoint
                        )
                        time.sleep(1)
                if not umounted_successfully:
                    log.warning(
                        '%s still busy at %s',
                        self.mountpoint, type(self).__name__
                    )
                else:
                    Path.remove(self.mountpoint)
