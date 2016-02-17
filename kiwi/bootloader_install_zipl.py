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
from .bootloader_install_base import BootLoaderInstallBase
from .command import Command
from .path import Path
from .logger import log

from .exceptions import(
    KiwiBootLoaderZiplInstallError
)


class BootLoaderInstallZipl(BootLoaderInstallBase):
    """
        zipl bootloader installation
    """
    def post_init(self, custom_args):
        self.custom_args = custom_args
        if not custom_args or 'boot_device' not in custom_args:
            raise KiwiBootLoaderZiplInstallError(
                'boot device node name required for zipl installation'
            )

        self.mountpoint = mkdtemp()
        self.is_mounted = False
        self.zipl_boot_device = custom_args['boot_device']

    def install(self):
        """
            install bootloader on self.device
        """
        log.info('Installing zipl on disk %s', self.device)

        self.__mount_boot_partition()

        bash_command = ' '.join(
            [
                'cd', self.mountpoint, '&&',
                'zipl', '-V', '-c', self.mountpoint + '/config',
                '-m', 'menu'
            ]
        )
        zipl_call = Command.run(
            ['bash', '-c', bash_command]
        )
        log.debug('zipl install succeeds with: %s', zipl_call.output)

        self.__umount_boot_partition()

    def __mount_boot_partition(self):
        Command.run(
            ['mount', self.zipl_boot_device, self.mountpoint]
        )
        self.is_mounted = True

    def __umount_boot_partition(self):
        Command.run(
            ['umount', self.mountpoint]
        )
        Path.remove(self.mountpoint)
        self.is_mounted = False

    def __del__(self):
        if self.is_mounted:
            log.info('Cleaning up %s instance', type(self).__name__)
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
                    '%s still busy at %s',
                    self.mountpoint, type(self).__name__
                )
            else:
                Path.remove(self.mountpoint)
