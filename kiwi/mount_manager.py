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
import logging
from textwrap import dedent
from typing import (
    List, Dict
)

# project
from kiwi.path import Path
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.exceptions import KiwiCommandError, KiwiUmountBusyError

log = logging.getLogger('kiwi')


class MountManager:
    """
    **Implements methods for mounting, umounting and mount checking**

    The caller is responsible for unmounting the device if the MountManager is
    used as is.

    The class also supports to be used as a context manager, where the device is
    unmounted once the context manager's with block is left

    * :param string device: device node name
    * :param string mountpoint: mountpoint directory name
    * :param dict attributes: optional attributes to store
    """
    def __init__(
        self, device: str, mountpoint: str = '',
        attributes: Dict[str, str] = {}
    ):
        self.device = device
        self.attributes = attributes
        if not mountpoint:
            self.mountpoint_tempdir = Temporary(
                prefix='kiwi_mount_manager.'
            ).new_dir()
            self.mountpoint = self.mountpoint_tempdir.name
        else:
            Path.create(mountpoint)
            self.mountpoint = mountpoint

    def __enter__(self) -> "MountManager":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.umount()

    def get_attributes(self) -> Dict[str, str]:
        """
        Return attributes dict for this mount manager
        """
        return self.attributes

    def bind_mount(self) -> None:
        """
        Bind mount the device to the mountpoint
        """
        if self.device and not self.is_mounted():
            Command.run(
                ['mount', '-n', '--bind', self.device, self.mountpoint]
            )

    def overlay_mount(self, lower: str) -> None:
        self.device = 'overlay'
        self.lower = lower
        self.upper = f'{self.mountpoint}_cow'
        self.work = f'{self.mountpoint}_work'
        Path.create(self.upper)
        Path.create(self.work)
        if not self.is_mounted():
            Command.run(
                [
                    'mount', '-t', 'overlay',
                    self.device, self.mountpoint, '-o',
                    'lowerdir={0},upperdir={1},workdir={2}'.format(
                        lower, self.upper, self.work
                    )
                ]
            )

    def tmpfs_mount(self) -> None:
        """
        tmpfs mount the device to the mountpoint
        """
        if not self.is_mounted():
            Command.run(
                ['mount', '-t', 'tmpfs', 'tmpfs', self.mountpoint]
            )

    def mount(self, options: List[str] = []) -> None:
        """
        Standard mount the device to the mountpoint

        :param list options: mount options
        """
        if self.device and not self.is_mounted():
            option_list = []
            if options:
                option_list = ['-o'] + options
            Command.run(
                ['mount'] + option_list + [self.device, self.mountpoint]
            )

    def umount_lazy(self) -> None:
        """
        Umount by the mountpoint directory in lazy mode

        Release the mount in any case, however the time when the mounted
        resource is released by the kernel depends on when the resource
        enters the non busy state
        """
        if self.is_mounted():
            Command.run(['umount', '-l', self.mountpoint])

    def umount(self, raise_on_busy: bool = True) -> bool:
        """
        Umount by the mountpoint directory

        Wait up to 10sec trying to umount. If the resource stays
        busy the call will raise an exception unless raise_on_busy
        is set to False. In case the umount failed and raise_on_busy
        is set to False, the method returns False to indicate the
        error condition.

        :return: True or False

        :rtype: bool
        """
        if self.is_mounted():
            umounted_successfully = False
            for busy in range(0, 5):
                try:
                    Command.run(['umount', self.mountpoint])
                    umounted_successfully = True
                    break
                except KiwiCommandError as err:
                    log.warning(
                        f'{busy} umount of {self.mountpoint} failed with: {err}'
                    )
                    time.sleep(1)
            if not umounted_successfully:
                try:
                    Command.run(['umount', '--lazy', self.mountpoint])
                    umounted_successfully = True
                except KiwiCommandError as err:
                    log.error(
                        f'umount of {self.mountpoint} failed with: {err}'
                    )
            if not umounted_successfully:
                if raise_on_busy:
                    lsof = Path.which('lsof', access_mode=os.X_OK)
                    if lsof:
                        open_files = Command.run(
                            [lsof, '+c', '0', self.mountpoint],
                            raise_on_error=False
                        )
                        open_files_info = 'Open files status:{0}{1}'.format(
                            os.linesep, open_files.output
                        )
                    else:
                        open_files_info = 'For further details install: lsof'
                    message = dedent('''\n
                        Failed to umount: {0}.

                        Your build host system is in an inconsistent state.
                        The cleanup of the created resource was not possible
                        because it is still busy. This resource and all nested
                        resources stays active on your host and needs a manual
                        cleanup.

                        Please do not use the intermediate state of the image
                        files created so far. There is no guarantee that the
                        produced results are valid.

                        {1}
                    ''')
                    raise KiwiUmountBusyError(
                        message.format(self.mountpoint, open_files_info)
                    )
                else:
                    log.warning(
                        '{0} still busy at {1}'.format(
                            self.mountpoint, type(self).__name__
                        )
                    )
                    # skip removing the mountpoint directory
                    return False
        return True

    def is_mounted(self) -> bool:
        """
        Check if mounted

        :return: True or False

        :rtype: bool
        """
        mountpoint_call = Command.run(
            command=['mountpoint', '-q', self.mountpoint],
            raise_on_error=False
        )
        return mountpoint_call.returncode == 0
