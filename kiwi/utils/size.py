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
import re
import math

from kiwi.exceptions import KiwiSizeError


class StringToSize:
    """
    **Performs size convertions from strings to numbers**
    """
    @staticmethod
    def to_bytes(size_value):
        """
        Convert the given string representig a size into the appropriate
        number of bytes.

        :param str size_value: a size in bytes or specified with m=MB or g=GB

        :return: the number of bytes represented by size_value string
        :rtype: int
        """
        size_format = r'^(\d+)([gGmM]{0,1})$'
        size = re.search(size_format, size_value)
        if not size:
            raise KiwiSizeError(
                'unsupported size format {0}, must match {1}'.format(
                    size_value, size_format
                )
            )
        size_base = int(size.group(1))
        size_unit = {'g': 3, 'm': 2}.get(size.group(2).lower())
        return size_base * math.pow(1024, size_unit) if size_unit \
            else size_base
