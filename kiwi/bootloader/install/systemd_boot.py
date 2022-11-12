# Copyright (c) 2022 Marcus Schäfer.  All rights reserved.
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
import logging
from typing import Dict

# project
from kiwi.bootloader.install.base import BootLoaderInstallBase

log = logging.getLogger('kiwi')


class BootLoaderInstallSystemdBoot(BootLoaderInstallBase):
    """
    **systemd-boot bootloader installation**
    """
    def post_init(self, custom_args: Dict):
        """
        systemd-boot post initialization method

        :param dict custom_args:
            Contains custom systemd-boot bootloader arguments
        """
        self.custom_args = custom_args

    def install_required(self):
        """
        Check if systemd-boot needs to install boot code

        systemd-boot supports EFI boot only and does not need to
        install boot code since it's expected that the firmware
        can read from the EFI partition

        :return: True or False

        :rtype: bool
        """
        return False

    def secure_boot_install(self):
        """
        Run shim installation for secure boot setup

        For systemd-boot this is currently skipped since details for
        secure boot are not yet clear
        """
        pass
