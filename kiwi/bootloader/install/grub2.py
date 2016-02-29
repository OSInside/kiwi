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
# project
from .base import BootLoaderInstallBase
from ...command import Command
from ...logger import log
from ...defaults import Defaults
from ...mount_manager import MountManager

from ...exceptions import(
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

        self.root_mount = MountManager(
            custom_args['root_device']
        )
        self.boot_mount = MountManager(
            custom_args['boot_device']
        )

    def install(self):
        """
            install bootloader on self.device
        """
        log.info('Installing grub2 on disk %s', self.device)

        if not self.root_mount.device == self.boot_mount.device:
            self.root_mount.mount()
            self.boot_mount.mount()
            module_directory = self.root_mount.mountpoint \
                + '/usr/lib/grub2/i386-pc'
            boot_directory = self.boot_mount.mountpoint
        else:
            self.root_mount.mount()
            module_directory = self.root_mount.mountpoint \
                + '/usr/lib/grub2/i386-pc'
            boot_directory = self.root_mount.mountpoint \
                + '/boot'

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

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        self.root_mount.umount()
        self.boot_mount.umount()
