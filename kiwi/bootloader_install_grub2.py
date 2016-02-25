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
from tempfile import mkdtemp
import time

# project
from .bootloader_install_base import BootLoaderInstallBase
from .command import Command
from .logger import log
from .path import Path
from .defaults import Defaults

from .exceptions import(
    KiwiBootLoaderGrubInstallError
)


class BootLoaderInstallGrub2(BootLoaderInstallBase):
    """
        grub2 bootloader installation for x86 bios platform
    """
    def post_init(self, custom_args):
        self.custom_args = custom_args
        if not custom_args or 'boot_device' not in custom_args:
            raise KiwiBootLoaderGrubInstallError(
                'boot device node name required for grub2 installation'
            )
        if not custom_args or 'root_device' not in custom_args:
            raise KiwiBootLoaderGrubInstallError(
                'root device node name required for grub2 installation'
            )

        self.mountpoint_root = mkdtemp()
        self.mountpoint_boot = mkdtemp()
        self.grub2_boot_device = custom_args['boot_device']
        self.grub2_root_device = custom_args['root_device']

        self.extra_boot_partition = False
        if not self.grub2_boot_device == self.grub2_root_device:
            self.extra_boot_partition = True

    def install(self):
        """
            install bootloader on self.device
        """
        log.info('Installing grub2 on disk %s', self.device)

        if self.extra_boot_partition:
            self.__mount_boot_partition()
            self.__mount_root_partition()
            module_directory = self.mountpoint_root + '/usr/lib/grub2/i386-pc'
            boot_directory = self.mountpoint_boot
        else:
            self.__mount_root_partition()
            module_directory = self.mountpoint_root + '/usr/lib/grub2/i386-pc'
            boot_directory = self.mountpoint_root + '/boot'

        Command.run(
            [
                'grub2-install',
                '--skip-fs-probe',
                '--directory', module_directory,
                '--boot-directory', boot_directory,
                '--target', 'i386-pc',
                '--modules', ' '.join(Defaults.get_grub_bios_modules()),
                self.device
            ]
        )

    def __mount_boot_partition(self):
        self.__mount(self.grub2_boot_device, self.mountpoint_boot)

    def __mount_root_partition(self):
        self.__mount(self.grub2_root_device, self.mountpoint_root)

    def __is_mounted(self, mountpoint):
        try:
            Command.run(['mountpoint', mountpoint])
            return True
        except Exception:
            return False

    def __mount(self, device, mountpoint):
        Command.run(['mount', device, mountpoint])
        return True

    def __umount(self, mountpoint):
        if self.__is_mounted(mountpoint):
            umounted_successfully = False
            for busy in [1, 2, 3]:
                try:
                    Command.run(['umount', mountpoint])
                    umounted_successfully = True
                    break
                except Exception:
                    log.warning(
                        '%d umount of %s failed, try again in 1sec',
                        busy, mountpoint
                    )
                    time.sleep(1)
            if not umounted_successfully:
                log.warning(
                    '%s still busy at %s', mountpoint, type(self).__name__
                )
                # skip removing the mountpoint directory
                return

        Path.remove(mountpoint)

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        self.__umount(self.mountpoint_root)
        self.__umount(self.mountpoint_boot)
