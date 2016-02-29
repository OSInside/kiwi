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
from collections import OrderedDict
from tempfile import NamedTemporaryFile

# project
from ..command import Command
from .device_provider import DeviceProvider
from .mapped_device import MappedDevice
from ..partitioner import Partitioner
from ..logger import log


class Disk(DeviceProvider):
    """
        implement storage disk and partition table setup
    """
    def __init__(self, table_type, storage_provider):
        # bind the underlaying block device providing class instance
        # to this object (e.g loop) if present. This is done to guarantee
        # the correct destructor order when the device should be released.
        self.storage_provider = storage_provider

        self.partition_map = {}
        self.partition_id_map = {}
        self.partition_id = {}
        self.is_mapped = False

        self.partitioner = Partitioner(
            table_type, storage_provider
        )

        self.table_type = table_type

    def get_device(self):
        """
            return names of partition devices, note that the mapping
            requires an explicit map() call
        """
        device_map = {}
        for partition_name, device_node in list(self.partition_map.items()):
            device_map[partition_name] = MappedDevice(
                device=device_node, device_provider=self
            )
        return device_map

    def is_loop(self):
        """
            returns if this disk is based on a loop device. The
            information is taken from the storage provider. If the
            storage provider is loop based the disk is it too
        """
        return self.storage_provider.is_loop()

    def create_root_partition(self, mbsize):
        self.partitioner.create('p.lxroot', mbsize, 't.linux')
        self.__add_to_map('root')
        self.__add_to_id_map('kiwi_RootPart')
        if 'kiwi_BootPart' not in self.partition_id_map:
            self.__add_to_id_map('kiwi_BootPart')

    def create_root_lvm_partition(self, mbsize):
        self.partitioner.create('p.lxlvm', mbsize, 't.lvm')
        self.__add_to_map('root')
        self.__add_to_id_map('kiwi_RootPart')
        self.__add_to_id_map('kiwi_RootPartVol', 'LVRoot')

    def create_root_raid_partition(self, mbsize):
        self.partitioner.create('p.lxraid', mbsize, 't.raid')
        self.__add_to_map('root')
        self.__add_to_id_map('kiwi_RootPart')
        self.__add_to_id_map('kiwi_RaidPart')
        self.__add_to_id_map('kiwi_RaidDev', '/dev/md0')

    def create_boot_partition(self, mbsize):
        self.partitioner.create('p.lxboot', mbsize, 't.linux')
        self.__add_to_map('boot')
        self.__add_to_id_map('kiwi_BootPart')

    def create_prep_partition(self, mbsize):
        self.partitioner.create('p.prep', mbsize, 't.prep')
        self.__add_to_map('prep')
        self.__add_to_id_map('kiwi_PrepPart')

    def create_efi_csm_partition(self, mbsize):
        self.partitioner.create('p.legacy', mbsize, 't.csm')
        self.__add_to_map('efi_csm')
        self.__add_to_id_map('kiwi_BiosGrub')

    def create_efi_partition(self, mbsize):
        self.partitioner.create('p.UEFI', mbsize, 't.efi')
        self.__add_to_map('efi')
        self.__add_to_id_map('kiwi_JumpPart')

    def activate_boot_partition(self):
        partition_id = None
        if 'prep' in self.partition_id:
            partition_id = self.partition_id['prep']
        elif 'boot' in self.partition_id:
            partition_id = self.partition_id['boot']
        elif 'root' in self.partition_id:
            partition_id = self.partition_id['root']

        if partition_id:
            self.partitioner.set_flag(partition_id, 'f.active')

    def wipe(self):
        """
            Zap (destroy) any GPT and MBR data structures if present
            For DASD disks create a new VTOC table
        """
        if 'dasd' in self.table_type:
            log.debug('Initialize DASD disk with new VTOC table')
            fdasd_input = NamedTemporaryFile()
            with open(fdasd_input.name, 'w') as vtoc:
                vtoc.write('y\n\nw\nq\n')
            bash_command = ' '.join(
                [
                    'cat', fdasd_input.name, '|',
                    'fdasd', '-f', self.storage_provider.get_device()
                ]
            )
            try:
                Command.run(
                    ['bash', '-c', bash_command]
                )
            except Exception:
                # unfortunately fdasd reports that it can't read in the
                # partition table which I consider a bug in fdasd. However
                # the table was correctly created and therefore we continue.
                # Problem is that we are not able to detect real errors
                # with the fdasd operation at that point.
                log.debug('potential fdasd errors were ignored')
        else:
            log.debug('Initialize %s disk', self.table_type)
            Command.run(
                [
                    'sgdisk', '--zap-all', self.storage_provider.get_device()
                ]
            )

    def map_partitions(self):
        if self.storage_provider.is_loop():
            Command.run(
                ['kpartx', '-s', '-a', self.storage_provider.get_device()]
            )
            self.is_mapped = True
        else:
            Command.run(
                ['partprobe', self.storage_provider.get_device()]
            )

    def get_partition_id_map(self):
        return OrderedDict(
            sorted(self.partition_id_map.items())
        )

    def __add_to_id_map(self, name, value=None):
        if not value:
            value = self.partitioner.get_id()
        self.partition_id_map[name] = value

    def __add_to_map(self, name):
        device_node = None
        partition_number = format(self.partitioner.get_id())
        if self.storage_provider.is_loop():
            device_base = os.path.basename(self.storage_provider.get_device())
            device_node = ''.join(
                ['/dev/mapper/', device_base, 'p', partition_number]
            )
        else:
            device = self.storage_provider.get_device()
            if device[-1].isdigit():
                device_node = ''.join(
                    [device, 'p', partition_number]
                )
            else:
                device_node = ''.join(
                    [device, partition_number]
                )
        if device_node:
            self.partition_map[name] = device_node
            self.partition_id[name] = partition_number

    def __del__(self):
        if self.storage_provider.is_loop() and self.is_mapped:
            log.info('Cleaning up %s instance', type(self).__name__)
            try:
                Command.run(
                    ['kpartx', '-s', '-d', self.storage_provider.get_device()]
                )
            except Exception:
                log.warning(
                    'cleanup of partition device maps failed, %s still busy',
                    self.storage_provider.get_device()
                )
