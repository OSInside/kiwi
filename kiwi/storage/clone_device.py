# Copyright (c) 2022 Marcus Schäfer.  All rights reserved.
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
import uuid
from typing import List

from kiwi.storage.device_provider import DeviceProvider
from kiwi.storage.mapped_device import MappedDevice
from kiwi.filesystem import FileSystem
from kiwi.command import Command
from kiwi.utils.block import BlockID
from kiwi.defaults import Defaults

from kiwi.exceptions import KiwiRaidSetupError


class CloneDevice(DeviceProvider):
    """
    **Implements device cloning**
    """
    def __init__(self, source_provider: DeviceProvider, root_dir: str):
        """
        Construct a new CloneDevice layout object

        :param object source_provider:
            Instance of class based on DeviceProvider
        :param str root_dir:
            Path to image root directory
        """
        self.source_provider = source_provider
        self.root_dir = root_dir

    def clone(self, target_devices: List[DeviceProvider]):
        """
        Clone source device to target device(s)

        :param list target_devices:
            List of target DeviceProvider instances
        """
        for target_device in target_devices:
            Command.run(
                [
                    'dd',
                    'if={0}'.format(self.source_provider.get_device()),
                    'of={0}'.format(target_device.get_device()),
                    'bs=1M'
                ]
            )
            clone_id = BlockID(target_device.get_device())
            target_filesystem = clone_id.get_filesystem()

            if target_filesystem in Defaults.get_filesystem_image_types():
                # Simple filesystem clones needs to be unique on the UUID
                # to avoid conflicts on the running system
                with FileSystem.new(target_filesystem, target_device) as fs:
                    fs.set_uuid()
            elif target_filesystem == 'LVM2_member':
                # Volume Group clones requires to be unique on the vgroup
                # name to avoid conflicts on the running system
                Command.run(
                    ['vgimportclone', target_device.get_device()]
                )
            elif target_filesystem == 'crypto_LUKS':
                # Device mapper clones based on the LUKS header needs to be
                # unique in the LUKS UUID to avoid conflicts on the running
                # system
                Command.run(
                    [
                        'cryptsetup', '-q', 'luksUUID',
                        target_device.get_device(), '--uuid',
                        format(uuid.uuid4())
                    ]
                )
            elif target_filesystem == 'linux_raid_member':
                # Device mapper clones based on the RAID superblock needs
                # to be unique in the UUID stored in the raid superblock
                # to avoid conflicts on the running system
                try:
                    mdadm_conf = f'{self.root_dir}/etc/mdadm.conf'
                    with open(mdadm_conf) as mdadm:
                        raid_config = mdadm.readline().split(' ')
                    md_device = raid_config[1]
                    md_name = raid_config[3].split('=')[1]
                    Command.run(
                        ['mdadm', '--stop', md_device]
                    )
                    Command.run(
                        [
                            'mdadm', '--assemble', '--update=uuid', '--name',
                            md_name, md_device, target_device.get_device()
                        ]
                    )
                    with FileSystem.new(
                        BlockID(md_device).get_filesystem(),
                        MappedDevice(md_device, target_device)
                    ) as fs:
                        fs.set_uuid()
                    Command.run(
                        ['mdadm', '--stop', md_device]
                    )
                    Command.run(
                        [
                            'mdadm', '--assemble', md_device,
                            self.source_provider.get_device()
                        ]
                    )
                except Exception as issue:
                    raise KiwiRaidSetupError(
                        f'Failed to update mdraid UUID: {issue}'
                    )
