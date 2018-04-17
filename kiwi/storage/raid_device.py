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
from kiwi.command import Command
from kiwi.storage.device_provider import DeviceProvider
from kiwi.storage.mapped_device import MappedDevice
from kiwi.logger import log

from kiwi.exceptions import (
    KiwiRaidSetupError
)


class RaidDevice(DeviceProvider):
    """
    **Implement raid setup on a storage device**

    :param object storage_provider: Instance of class based on DeviceProvider
    """
    def __init__(self, storage_provider):
        # bind the underlaying block device providing class instance
        # to this object (e.g loop) if present. This is done to guarantee
        # the correct destructor order when the device should be released.
        self.storage_provider = storage_provider

        self.raid_level_map = {
            'mirroring': '1',
            'striping': '0'
        }
        self.raid_device = None

    def get_device(self):
        """
        Instance of MappedDevice providing the raid device

        :return: mapped raid device

        :rtype: MappedDevice
        """
        if self.raid_device:
            return MappedDevice(
                device=self.raid_device, device_provider=self
            )

    def create_degraded_raid(self, raid_level):
        """
        Create a raid array in degraded mode with one device missing.
        This only works in the raid levels 0(striping) and 1(mirroring)

        :param string raid_level: raid level name
        """
        if raid_level not in self.raid_level_map:
            raise KiwiRaidSetupError(
                'Only raid levels 0(striping) and 1(mirroring) are supported'
            )
        raid_device = None
        for raid_id in range(9):
            raid_device = '/dev/md' + format(raid_id)
            if os.path.exists(raid_device):
                raid_device = None
            else:
                break
        if not raid_device:
            raise KiwiRaidSetupError(
                'Could not find free raid device in range md0-8'
            )
        log.info(
            'Creating raid array in %s mode as %s',
            raid_level, raid_device
        )
        Command.run(
            [
                'mdadm', '--create', '--run', raid_device,
                '--level', self.raid_level_map[raid_level],
                '--raid-disks', '2',
                self.storage_provider.get_device(), 'missing'
            ]
        )
        self.raid_device = raid_device

    def create_raid_config(self, filename):
        """
        Create mdadm config file from mdadm request

        :param string filename: config file name
        """
        mdadm_call = Command.run(
            ['mdadm', '-Db', self.raid_device]
        )
        with open(filename, 'w') as mdadmconf:
            mdadmconf.write(mdadm_call.output)

    def is_loop(self):
        """
        Check if storage provider is loop based

        Return loop status from base storage provider

        :return: True or False

        :rtype: bool
        """
        return self.storage_provider.is_loop()

    def __del__(self):
        if self.raid_device:
            log.info('Cleaning up %s instance', type(self).__name__)
            try:
                Command.run(
                    ['mdadm', '--stop', self.raid_device]
                )
            except Exception:
                log.warning(
                    'Shutdown of raid device failed, %s still busy',
                    self.raid_device
                )
