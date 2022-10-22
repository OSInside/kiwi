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
from kiwi.container.setup.base import ContainerSetupBase


class ContainerSetupOCI(ContainerSetupBase):
    """
    Oci container setup
    """
    def post_init(self, custom_args):
        """
        Post initialization method

        Store custom arguments

        :param list custom_args: custom bootloader arguments
        """
        if custom_args:
            self.custom_args = custom_args

    def setup(self):
        """
        Setup system for use with docker
        """

        services_to_deactivate = [
            'device-mapper.service',
            'kbd.service',
            'swap.service',
            'udev.service',
            'proc-sys-fs-binfmt_misc.automount'
        ]

        self.deactivate_bootloader_setup()
        self.deactivate_root_filesystem_check()
        self.setup_root_console()

        for service in services_to_deactivate:
            self.deactivate_systemd_service(service)
