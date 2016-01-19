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
from bootloader_config_grub2 import BootLoaderConfigGrub2
from bootloader_config_isolinux import BootLoaderConfigIsoLinux

from exceptions import (
    KiwiBootLoaderConfigSetupError
)


class BootLoaderConfig(object):
    """
        BootLoaderConfig factory
    """
    def __new__(self, name, xml_state, root_dir):
        if name == 'grub2':
            return BootLoaderConfigGrub2(
                xml_state, root_dir
            )
        elif name == 'isolinux':
            return BootLoaderConfigIsoLinux(
                xml_state, root_dir
            )
        else:
            raise KiwiBootLoaderConfigSetupError(
                'Support for %s bootloader config not implemented' % name
            )
