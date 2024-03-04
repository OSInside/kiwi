# Copyright (c) 2024 SUSE Software Solutions Germany GmbH.  All rights reserved.
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


class BootLoaderInstallZipl(BootLoaderInstallBase):
    """
    **zipl bootloader installation**
    """
    def post_init(self, custom_args: Dict):
        """
        zipl post initialization method

        :param dict custom_args: unused
        """
        self.custom_args = custom_args

    def install_required(self) -> bool:
        """
        Check if zipl needs to install boot code

        zipl requires boot code installation, but it is done as
        part of the BLS implementation in bootloader/config/zipl.py
        Thus this method always returns: False

        :return: False

        :rtype: bool
        """
        return False

    def secure_boot_install(self):
        """
        Run shim installation for secure boot setup

        For zipl this is skipped since details for
        secure boot are not yet clear.
        """
        pass
