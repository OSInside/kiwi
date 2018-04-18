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
from kiwi.command import Command
from kiwi.exceptions import (
    KiwiDeviceProviderError
)


class DeviceProvider(object):
    """
    **Base class for any class providing storage devices**
    """
    def get_device(self):
        """
        Representation of device nodes

        Could provide one ore more devices representing the storage
        Implementation in specialized device provider class
        """
        raise KiwiDeviceProviderError(
            'No storage device(s) provided'
        )

    def get_uuid(self, device):
        """
        UUID of device

        :param string device: node name

        :return: UUID from blkid

        :rtype: str
        """
        uuid_call = Command.run(
            ['blkid', device, '-s', 'UUID', '-o', 'value']
        )
        return uuid_call.output.rstrip('\n')

    def get_byte_size(self, device):
        """
        Size of device in bytes

        :param string device: node name

        :return: byte value from blockdev

        :rtype: int
        """
        blockdev_call = Command.run(
            ['blockdev', '--getsize64', device]
        )
        return int(blockdev_call.output.rstrip('\n'))

    def is_loop(self):
        """
        Check if device provider is loop based

        By default this is always False and needs an implementation
        in the the specialized device provider class

        :return: True or False

        :rtype: bool
        """
        return False
