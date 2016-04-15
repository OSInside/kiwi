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
from .device_provider import DeviceProvider
from ..exceptions import (
    KiwiMappedDeviceError
)


class MappedDevice(DeviceProvider):
    """
    Hold a reference on a single device

    Attributes

    * :attr:`device_provider`
        Instance of class based on DeviceProvider

    * :attr:`device`
        Device node name
    """
    def __init__(self, device, device_provider):
        if not os.path.exists(device):
            raise KiwiMappedDeviceError(
                'Device %s does not exist' % device
            )
        self.device_provider = device_provider
        self.device = device

    def get_device(self):
        """
        Mapped device node name

        :return: device node name
        :rtype: string
        """
        return self.device

    def is_loop(self):
        """
        Check if storage provider is loop based

        Return loop status from base storage provider

        :rtype: bool
        """
        return self.device_provider.is_loop()
