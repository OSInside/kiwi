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
from kiwi.boot.image.builtin_kiwi import BootImageKiwi
from kiwi.boot.image.dracut import BootImageDracut

from kiwi.exceptions import (
    KiwiBootImageSetupError
)


class BootImage(object):
    """
        BootImge factory
    """
    def __new__(self, xml_state, target_dir, root_dir=None):
        initrd_system = xml_state.build_type.get_initrd_system()
        if not initrd_system:
            initrd_system = 'kiwi'
        if initrd_system == 'kiwi':
            return BootImageKiwi(xml_state, target_dir)
        elif initrd_system == 'dracut':
            return BootImageDracut(xml_state, target_dir, root_dir)
        else:
            raise KiwiBootImageSetupError(
                'Support for %s initrd system not implemented' % initrd_system
            )
