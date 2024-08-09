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
import logging

# project
from kiwi.storage.device_provider import DeviceProvider

from kiwi.exceptions import KiwiTargetDeviceSetupError

log = logging.getLogger('kiwi')


class TargetDevice(DeviceProvider):
    """
    **Map direct target device for block operations**

    :param string filename: target device name
    :param int filesize_mbytes: unused
    :param int blocksize_bytes: unused
    """
    def __init__(
        self, filename: str, filesize_mbytes: int = None,
        blocksize_bytes: int = None
    ):
        self.node_name = filename
        if not os.path.exists(filename):
            raise KiwiTargetDeviceSetupError(
                'Target device {self.node_name} does not exist'
            )
        self.filename = filename
        self.filesize_mbytes = filesize_mbytes
        self.blocksize_bytes = blocksize_bytes

    def __enter__(self):
        return self

    def get_device(self) -> str:
        """
        Device node name

        :return: device node name

        :rtype: str
        """
        return self.node_name

    def create(self, overwrite: bool = True):
        """
        Target device is expected to exist, the create method
        becomes a noop in this case

        :param bool overwrite: unused
        """
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass
