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
from kiwi.storage.device_provider import DeviceProvider
from kiwi.exceptions import (
    KiwiMappedDeviceError
)


class MappedDevice(DeviceProvider):
    """
    **Hold a reference on a single device**

    :param object device_provider: Instance of class based on DeviceProvider
    :param string device: Device node name
    """
    def __init__(self, device: str, device_provider: DeviceProvider):
        if not os.path.exists(device):
            raise KiwiMappedDeviceError(
                'Device %s does not exist' % device
            )
        self.device_provider = device_provider
        self.device = device

    def get_device(self) -> str:
        """
        Mapped device node name

        :return: device node name

        :rtype: str
        """
        return self.device

    def is_loop(self) -> bool:
        """
        Check if storage provider is loop based

        Return loop status from base storage provider

        :return: True or False

        :rtype: bool
        """
        return self.device_provider.is_loop()
