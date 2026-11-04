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
from typing import Dict, Optional

# project
from kiwi.xml_state import XMLState
from kiwi.storage.device_provider import DeviceProvider


class BootLoaderInstallBase:
    """
    **Base class for bootloader installation on device**

    :param string root_dir: root directory path name
    :param object device_provider: instance of :class:`DeviceProvider`
    :param dict custom_args: custom arguments dictionary
    """

    def __init__(
        self,
        xml_state: XMLState,
        root_dir: str,
        device_provider: DeviceProvider,
        custom_args: Optional[Dict] = None,
    ) -> None:
        self.xml_state = xml_state
        self.root_dir = root_dir
        self.device_provider = device_provider

        self.device = self.device_provider.get_device()

        self.post_init(custom_args)

    def post_init(self, custom_args: Optional[Dict]) -> None:
        """
        Post initialization method

        Store custom arguments by default

        :param dict custom_args: custom bootloader arguments
        """
        self.custom_args = custom_args

    def install_required(self) -> bool:
        """
        Check if bootloader needs to be installed

        Implementation in specialized bootloader install class required
        """
        raise NotImplementedError

    def install(self) -> None:
        """
        Install bootloader on self.device

        Implementation in specialized bootloader install class required
        """
        raise NotImplementedError

    def secure_boot_install(self) -> None:
        """
        Run shim-install in self.device for secure boots

        Implementation in specialized bootloader install class required
        """
        raise NotImplementedError

    def set_disk_password(self, password: str) -> None:
        """
        Include crypto mount credentials

        Implementation in specialized bootloader install class optional
        """
        pass
