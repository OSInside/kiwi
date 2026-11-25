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
from typing import Any, Dict, Optional

# project
from kiwi.command import Command

from kiwi.exceptions import KiwiContainerSetupError


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

    def __init__(
        self, root_dir: str, custom_args: Optional[Dict] = None
    ) -> None:
        if not os.path.exists(root_dir):
            raise KiwiContainerSetupError(
                f'Container root directory {root_dir} does not exist'
            )
        self.root_dir = root_dir
        self.custom_args: Dict[str, Any] = custom_args or {}
        if 'container_name' not in self.custom_args:
            self.custom_args['container_name'] = 'system-container'
        self.post_init(custom_args)

    def post_init(self, custom_args: Optional[Dict]) -> None:
        """
        Post initialization method

        Implementation in specialized container setup class

        :param list custom_args: unused
        """
        pass

    def setup(self) -> None:
        """
        Setup container metadata

        Implementation in specialized bootloader class required
        """
        raise NotImplementedError

    def deactivate_bootloader_setup(self) -> None:
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
                    'LOADER_TYPE': 'LOADER_TYPE="none"',
                },
            )

    def deactivate_root_filesystem_check(self) -> None:
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
                boot_setup, {'ROOTFS_BLKDEV': 'ROOTFS_BLKDEV="/dev/null"'}
            )

    def deactivate_systemd_service(self, name: str) -> None:
        """
        Container system services setup

        Init systems among others also controls services which
        starts at boot time. A container does not really boot.
        Thus some services needs to be deactivated

        :param string name: systemd service name
        """
        service_file = self.root_dir + '/usr/lib/systemd/system/' + name
        if os.path.islink(service_file) and (
            os.readlink(service_file) == '/dev/null'
        ):
            # service is already deactivated, e.g by a former
            # container setup on the same root tree. Replacing the
            # link would change its timestamp in the container
            return
        if os.path.exists(service_file):
            try:
                Command.run(['ln', '-s', '-f', '/dev/null', service_file])
            except Exception as e:
                raise KiwiContainerSetupError(
                    f'Failed to deactivate service {name}: {format(e)}'
                )

    def setup_root_console(self) -> None:
        """
        Container console setup

        /dev/console should be allowed to login by root
        """
        securetty = self.root_dir + '/etc/securetty'
        if not os.path.exists(securetty):
            with open(securetty, 'w'):
                pass
        self._update_config(securetty, {'console': 'console'})

    def get_container_name(self) -> str:
        """
        Container name

        :return: name
        :rtype: str
        """
        return self.custom_args['container_name']

    def _update_config(
        self, filename: str, update_record: Dict[str, str]
    ) -> None:
        """
        Update the given config file with the given records. The
        file is only written if its content changes, such that a
        container setup on an already setup root tree, e.g by
        kiwi system create after kiwi system build, does not
        change the data and the timestamp of the file
        """
        with open(filename, 'r') as config:
            current_data = config.read()
        data = current_data.splitlines()

        sorted_record = collections.OrderedDict(sorted(update_record.items()))
        for current_value, new_value in list(sorted_record.items()):
            entry_found = False
            for index in range(0, len(data)):
                line = data[index]
                if line.startswith(current_value):
                    entry_found = True
                    data[index] = new_value
            if not entry_found:
                data.append(new_value)

        new_data = '%s\n' % '\n'.join(data)
        if new_data != current_data:
            with open(filename, 'w') as config:
                config.write(new_data)
