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
import logging
import copy

# project
from kiwi.defaults import Defaults
from kiwi.utils.sync import DataSync
from kiwi.mount_manager import MountManager
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiFileSystemSyncError
)

log = logging.getLogger('kiwi')


class FileSystemBase:
    """
    **Implements base class for filesystem interface**

    :param object device_provider:
        Instance of a class based on DeviceProvider
        required for filesystems which needs a block device for
        creation. In most cases the DeviceProvider is a LoopDevice
    :param string root_dir: root directory path name
    :param dict custom_args: custom filesystem arguments
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

        self.custom_args = {}
        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Store dictionary of custom arguments if not empty. This
        overrides the default custom argument hash

        :param dict custom_args: custom arguments

            .. code:: python

                {
                    'create_options': ['option'],
                    'mount_options': ['option'],
                    'meta_data': {
                        'key': 'value'
                    }
                }
        """
        if custom_args:
            self.custom_args = copy.deepcopy(custom_args)

        if not self.custom_args.get('create_options'):
            self.custom_args['create_options'] = []

        if not self.custom_args.get('meta_data'):
            self.custom_args['meta_data'] = {}

        if not self.custom_args.get('mount_options'):
            self.custom_args['mount_options'] = []

        if not self.custom_args.get('fs_attributes'):
            self.custom_args['fs_attributes'] = []

    def create_on_device(self, label=None):
        """
        Create filesystem on block device

        Implement in specialized filesystem class for filesystems which
        requires a block device for creation, e.g ext4.

        :param string label: label name
        """
        raise NotImplementedError

    def create_on_file(self, filename, label=None, exclude=None):
        """
        Create filesystem from root data tree

        Implement in specialized filesystem class for filesystems which
        requires a data tree for creation, e.g squashfs.

        :param string filename: result file path name
        :param string label: label name
        :param list exclude: list of exclude dirs/files
        """
        raise NotImplementedError

    def get_mountpoint(self):
        """
        Provides mount point directory

        Effective use of the directory is guaranteed only after sync_data

        :return: directory path name

        :rtype: string
        """
        if self.filesystem_mount:
            return self.filesystem_mount.mountpoint

    def sync_data(self, exclude=None):
        """
        Copy root data tree into filesystem

        :param list exclude: list of exclude dirs/files
        """
        if not self.root_dir:
            raise KiwiFileSystemSyncError(
                'no root directory specified'
            )
        if not os.path.exists(self.root_dir):
            raise KiwiFileSystemSyncError(
                'given root directory %s does not exist' % self.root_dir
            )
        self.filesystem_mount = MountManager(
            device=self.device_provider.get_device()
        )
        self.filesystem_mount.mount(
            self.custom_args['mount_options']
        )
        self._apply_attributes()
        data = DataSync(
            self.root_dir, self.filesystem_mount.mountpoint
        )
        data.sync_data(
            exclude=exclude, options=Defaults.get_sync_options()
        )

    def umount(self):
        """
        Umounts the filesystem in case it is mounted, does nothing otherwise
        """
        if self.filesystem_mount:
            log.info('umount %s instance', type(self).__name__)
            self.filesystem_mount.umount()
            self.filesystem_mount = None

    def _apply_attributes(self):
        """
        Apply filesystem attributes
        """
        attribute_map = {
            'synchronous-updates': '+S',
            'no-copy-on-write': '+C'
        }
        for attribute in self.custom_args['fs_attributes']:
            if attribute_map.get(attribute):
                log.info(
                    '--> setting {0} for {1}'.format(
                        attribute, self.filesystem_mount.mountpoint
                    )
                )
                Command.run(
                    [
                        'chattr', attribute_map.get(attribute),
                        self.filesystem_mount.mountpoint
                    ]
                )

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        self.umount()
