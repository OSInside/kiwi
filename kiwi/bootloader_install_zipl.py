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
from bootloader_install_base import BootLoaderInstallBase
from command import Command
from logger import log

from exceptions import(
    KiwiBootLoaderZiplInstallError
)


class BootLoaderInstallZipl(BootLoaderInstallBase):
    """
        zipl bootloader installation
    """
    def post_init(self, custom_args):
        self.custom_args = custom_args
        if not custom_args or 'boot_mount_path' not in custom_args:
            raise KiwiBootLoaderZiplInstallError(
                'active boot mount point required for zipl installation'
            )

        self.zipl_boot_mount_path = custom_args['boot_mount_path']

    def install(self):
        """
            install bootloader on self.device
        """
        log.info('Installing zipl on disk %s', self.device)
        bash_command = ' '.join(
            [
                'cd', self.zipl_boot_mount_path, '&&',
                'zipl', '-V', '-c', self.zipl_boot_mount_path + '/config',
                '-m', 'menu'
            ]
        )
        Command.run(
            ['bash', '-c', bash_command]
        )
