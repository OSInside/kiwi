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
from .grub2 import BootLoaderConfigGrub2
from .isolinux import BootLoaderConfigIsoLinux
from .zipl import BootLoaderConfigZipl

from ...exceptions import (
    KiwiBootLoaderConfigSetupError
)


class BootLoaderConfig(object):
    """
    BootLoaderConfig factory

    Attributes

    * :attr:`name`
        bootloader name

    * :attr:`xml_state`
        Instance of XMLState

    * :attr:`root_dir`
        root directory path name

    * :attr:`custom_args`
        list of custom bootloader arguments
    """
    def __new__(self, name, xml_state, root_dir, custom_args=None):
        if name == 'grub2':
            return BootLoaderConfigGrub2(
                xml_state, root_dir, custom_args
            )
        elif name == 'grub2_s390x_emu':
            return BootLoaderConfigZipl(
                xml_state, root_dir, custom_args
            )
        elif name == 'isolinux':
            return BootLoaderConfigIsoLinux(
                xml_state, root_dir, custom_args
            )
        else:
            raise KiwiBootLoaderConfigSetupError(
                'Support for %s bootloader config not implemented' % name
            )
