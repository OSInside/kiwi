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
import random
import struct

# project
from kiwi.storage.device_provider import DeviceProvider


class SystemIdentifier:
    """
    **Create a random ID to identify the system**

    The information is used to create the mbrid file as an example

    :param str image_id: hex identifier string
    """
    def __init__(self):
        self.image_id = None

    def get_id(self) -> str:
        """
        Current hex identifier

        :return: hex id

        :rtype: str
        """
        return self.image_id

    def calculate_id(self) -> None:
        """
        Calculate random hex id

        Using 4 tuples of rand in range from 1..0xfe
        """
        self.image_id = '0x%02x%02x%02x%02x' % (
            self._rand(), self._rand(), self._rand(), self._rand()
        )

    def write(self, filename: str) -> None:
        """
        Write current hex identifier to file

        :param str filename: file path name
        """
        with open(filename, 'w') as identifier:
            identifier.write('%s\n' % self.image_id)

    def write_to_disk(self, device_provider: DeviceProvider) -> None:
        """
        Write current hex identifier to MBR at offset 0x1b8 on disk

        :param object device_provider: Instance based on DeviceProvider
        """
        if self.image_id:
            packed_id = struct.pack('<I', int(self.image_id, 16))
            with open(device_provider.get_device(), 'wb') as disk:
                disk.seek(440, 0)
                disk.write(packed_id)

    def _rand(self):
        return random.randrange(1, 0xfe)
