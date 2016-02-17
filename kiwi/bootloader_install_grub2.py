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
from tempfile import NamedTemporaryFile
from tempfile import mkdtemp

# project
from .bootloader_install_base import BootLoaderInstallBase
from .command import Command
from .logger import log
from .path import Path


class BootLoaderInstallGrub2(BootLoaderInstallBase):
    """
        grub2 bootloader installation
    """
    def post_init(self, custom_args):
        self.custom_args = custom_args
        self.temporary_boot_dir = None

    def install(self):
        """
            install bootloader on self.device
        """
        log.info('Installing grub2 on disk %s', self.device)
        device_map_file = NamedTemporaryFile()
        with open(device_map_file.name, 'w') as device_map:
            device_map.write('(hd0) %s\n' % self.device)

        # The following copy action is only needed because grub2-probe
        # is not able to resolve the canonical path of the boot directory
        # if it lives on e.g a tmpfs. However building an image in a tmpfs
        # is done pretty often to increase the build performance. In order
        # to make grub happy we have to copy out the boot data with the
        # hope that /boot of the build host system is not on a filesystem
        # which causes grub2-probe to fail again
        self.temporary_boot_dir = mkdtemp(prefix='kiwi_bootloader.')
        Command.run(
            ['cp', '-a', self.root_dir + '/boot/', self.temporary_boot_dir]
        )

        Command.run(
            [
                'grub2-bios-setup', '-f',
                '-d', self.temporary_boot_dir + '/boot/grub2/i386-pc',
                '-m', device_map_file.name,
                self.device
            ]
        )

    def __del__(self):
        if self.temporary_boot_dir:
            log.info('Cleaning up %s instance', type(self).__name__)
            Path.wipe(self.temporary_boot_dir)
