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
from kiwi.bootloader.install.base import BootLoaderInstallBase
from kiwi.command import Command
from kiwi.logger import log
from kiwi.mount_manager import MountManager

from kiwi.exceptions import (
    KiwiBootLoaderZiplInstallError
)


class BootLoaderInstallZipl(BootLoaderInstallBase):
    """
    **zipl bootloader installation**
    """
    def post_init(self, custom_args):
        """
        zipl post initialization method

        :param dict custom_args:
            Contains custom zipl bootloader arguments

            .. code:: python

                {'boot_device': string}

        """
        self.custom_args = custom_args
        if not custom_args or 'boot_device' not in custom_args:
            raise KiwiBootLoaderZiplInstallError(
                'boot device node name required for zipl installation'
            )

        self.boot_mount = MountManager(
            custom_args['boot_device']
        )

    def install_required(self):
        """
        Check if zipl has to be installed

        Always required

        :return: True

        :rtype: bool
        """
        return True

    def install(self):
        """
        Install bootloader on self.device
        """
        log.info('Installing zipl on disk %s', self.device)

        self.boot_mount.mount()

        bash_command = ' '.join(
            [
                'cd', self.boot_mount.mountpoint, '&&',
                'zipl', '-V', '-c', self.boot_mount.mountpoint + '/config',
                '-m', 'menu'
            ]
        )
        zipl_call = Command.run(
            ['bash', '-c', bash_command]
        )
        log.debug('zipl install succeeds with: %s', zipl_call.output)

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        self.boot_mount.umount()
