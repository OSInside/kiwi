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
from .grub2 import BootLoaderInstallGrub2
from .zipl import BootLoaderInstallZipl

from ...exceptions import (
    KiwiBootLoaderInstallSetupError
)


class BootLoaderInstall(object):
    """
    BootLoaderInstall factory

    Attributes

    * :attr:`name`
        bootloader name

    * :attr:`root_dir`
        root directory path name

    * :attr:`device_provider`
        Instance of class based on DeviceProvider

    * :attr:`custom_args`
        list of custom bootloader arguments
    """
    def __new__(self, name, root_dir, device_provider, custom_args=None):
        if name == 'grub2':
            return BootLoaderInstallGrub2(
                root_dir, device_provider, custom_args
            )
        elif name == 'grub2_s390x_emu':
            return BootLoaderInstallZipl(
                root_dir, device_provider, custom_args
            )
        else:
            raise KiwiBootLoaderInstallSetupError(
                'Support for %s bootloader installation not implemented' % name
            )
