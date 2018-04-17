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
import os

# project
from .exceptions import (
    KiwiPrivilegesError
)


class Privileges(object):
    """
    **Implements check for root privileges**
    """
    @classmethod
    def check_for_root_permissions(self):
        """
        Check if we are effectively root on the system. If not
        an exception is thrown

        :return: True or raise an Exception

        :rtype: bool
        """
        if os.geteuid() != 0:
            raise KiwiPrivilegesError(
                'operation requires root permissions'
            )
        return True
