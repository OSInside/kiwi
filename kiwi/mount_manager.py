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
from tempfile import mkdtemp

# project
from .command import Command
from .path import Path


class MountManager(object):
    """
    **Implements methods for mounting, umounting and mount checking**

    If a MountManager instance is used to mount a device the caller
    must care for the time when umount needs to be called. The class
    does not automatically release the mounted device, which is
    intentional

    * :param string device: device node name
    * :param string mountpoint: mountpoint directory name
    """
    def __init__(self, device, mountpoint=None):
        self.device = device
        self.mountpoint_created_by_mount_manager = False
        if not mountpoint:
            self.mountpoint = mkdtemp(prefix='kiwi_mount_manager.')
            self.mountpoint_created_by_mount_manager = True
        else:
            self.mountpoint = mountpoint

    def bind_mount(self):
        """
        Bind mount the device to the mountpoint
        """
        if not self.is_mounted():
            Command.run(
                ['mount', '-n', '--bind', self.device, self.mountpoint]
            )

    def mount(self, options=None):
        """
        Standard mount the device to the mountpoint

        :param list options: mount options
        """
        if not self.is_mounted():
            option_list = []
            if options:
                option_list = ['-o'] + options
            Command.run(
                ['mount'] + option_list + [self.device, self.mountpoint]
            )

    def umount_lazy(self):
        """
        Umount by the mountpoint directory in lazy mode

        Release the mount in any case, however the time when the mounted
        resource is released by the kernel depends on when the resource
        enters the non busy state
        """
        if self.is_mounted():
            Command.run(['umount', '-l', self.mountpoint])

    def umount(self):
        """
        Umount by the mountpoint directory

        If the resource is busy the call will return False

        :return: True or False

        :rtype: bool
        """
        from .logger import log
        if self.is_mounted():
            umounted_successfully = False
            for busy in [1, 2, 3]:
                try:
                    Command.run(['umount', self.mountpoint])
                    umounted_successfully = True
                    break
                except Exception:
                    log.warning(
                        '%d umount of %s failed, try again in 1sec',
                        busy, self.mountpoint
                    )
                    time.sleep(1)
            if not umounted_successfully:
                log.warning(
                    '%s still busy at %s', self.mountpoint, type(self).__name__
                )
                # skip removing the mountpoint directory
                return False

        return True

    def is_mounted(self):
        """
        Check if mounted

        :return: True or False

        :rtype: bool
        """
        mountpoint_call = Command.run(
            command=['mountpoint', '-q', self.mountpoint],
            raise_on_error=False
        )
        if mountpoint_call.returncode == 0:
            return True
        else:
            return False

    def __del__(self):
        if self.mountpoint_created_by_mount_manager and not self.is_mounted():
            Path.wipe(self.mountpoint)
