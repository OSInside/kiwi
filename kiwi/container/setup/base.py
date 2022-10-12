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
import collections
import os

# project
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiContainerSetupError
)


class ContainerSetupBase:
    """
    Base class for setting up the root system to create
    a container image from for e.g docker. The methods here
    are generic to linux systems following the FHS standard
    and modern enough e.g based on systemd

    Attributes

    * :attr:`root_dir`
        root directory path name

    * :attr:`custom_args`
        dict of custom arguments
    """
    def __init__(self, root_dir, custom_args=None):
        if not os.path.exists(root_dir):
            raise KiwiContainerSetupError(
                'Container root directory %s does not exist' % root_dir
            )
        self.root_dir = root_dir
        self.custom_args = custom_args or {}
        if 'container_name' not in self.custom_args:
            self.custom_args['container_name'] = 'system-container'
        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Implementation in specialized container setup class

        :param list custom_args: unused
        """
        pass

    def setup(self):
        """
        Setup container metadata

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def deactivate_bootloader_setup(self):
        """
        Container bootloader setup

        Tell the system there is no bootloader configuration
        it needs to care for. A container does not boot
        """
        bootloader_setup = self.root_dir + '/etc/sysconfig/bootloader'
        if os.path.exists(bootloader_setup):
            self._update_config(
                bootloader_setup,
                {
                    'LOADER_LOCATION': 'LOADER_LOCATION="none"',
                    'LOADER_TYPE': 'LOADER_TYPE="none"'
                }
            )

    def deactivate_root_filesystem_check(self):
        """
        Container filesystem check setup

        The root filesystem of a container could be an overlay
        or a mapped device. In any case it should not be checked
        for consistency as this is should be done by the container
        infrastructure
        """
        boot_setup = self.root_dir + '/etc/sysconfig/boot'
        if os.path.exists(boot_setup):
            self._update_config(
                boot_setup,
                {
                    'ROOTFS_BLKDEV': 'ROOTFS_BLKDEV="/dev/null"'
                }
            )

    def deactivate_systemd_service(self, name):
        """
        Container system services setup

        Init systems among others also controls services which
        starts at boot time. A container does not really boot.
        Thus some services needs to be deactivated

        :param string name: systemd service name
        """
        service_file = self.root_dir + '/usr/lib/systemd/system/' + name
        if os.path.exists(service_file):
            try:
                Command.run(
                    ['ln', '-s', '-f', '/dev/null', service_file]
                )
            except Exception as e:
                raise KiwiContainerSetupError(
                    'Failed to deactivate service %s: %s' %
                    (name, format(e))
                )

    def setup_root_console(self):
        """
        Container console setup

        /dev/console should be allowed to login by root
        """
        securetty = self.root_dir + '/etc/securetty'
        if not os.path.exists(securetty):
            with open(securetty, 'w'):
                pass
        self._update_config(
            securetty,
            {
                'console': 'console'
            }
        )

    def get_container_name(self):
        """
        Container name

        :return: name
        :rtype: str
        """
        return self.custom_args['container_name']

    def _update_config(self, filename, update_record):
        data = []
        with open(filename, 'r') as config:
            data = config.read().rsplit('\n')

        sorted_record = collections.OrderedDict(
            sorted(update_record.items())
        )
        for current_value, new_value in list(sorted_record.items()):
            entry_found = False
            for index in range(0, len(data)):
                line = data[index]
                if line.startswith(current_value):
                    entry_found = True
                    data[index] = new_value
            if not entry_found:
                data.append(new_value)

        with open(filename, 'w') as config:
            config.write('%s\n' % '\n'.join(data))
