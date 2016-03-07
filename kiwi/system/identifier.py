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


class SystemIdentifier(object):
    """
        Create a random ID to identify the system. The information
        is used to create the mbrid file as an example
    """
    def __init__(self):
        self.image_id = None

    def get_id(self):
        return self.image_id

    def calculate_id(self):
        self.image_id = '0x%02x%02x%02x%02x' % (
            self.__rand(), self.__rand(), self.__rand(), self.__rand()
        )

    def write(self, filename):
        with open(filename, 'w') as identifier:
            identifier.write('%s\n' % self.image_id)

    def write_to_disk(self, device_provider):
        if self.image_id:
            packed_id = struct.pack('<I', int(self.image_id, 16))
            with open(device_provider.get_device(), 'wb') as disk:
                disk.seek(440, 0)
                disk.write(packed_id)

    def __rand(self):
        return random.randrange(1, 0xfe)
