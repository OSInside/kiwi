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
from collections import OrderedDict
from tempfile import NamedTemporaryFile

# project
from kiwi.command import Command
from kiwi.storage.device_provider import DeviceProvider
from kiwi.storage.mapped_device import MappedDevice
from kiwi.partitioner import Partitioner

log = logging.getLogger('kiwi')


class Disk(DeviceProvider):
    """
    **Implements storage disk and partition table setup**

    :param string table_type: Partition table type name
    :param object storage_provider: Instance of class based on DeviceProvider
    :param int start_sector: sector number
    """
    def __init__(self, table_type, storage_provider, start_sector=None):
        # bind the underlaying block device providing class instance
        # to this object (e.g loop) if present. This is done to guarantee
        # the correct destructor order when the device should be released.
        self.storage_provider = storage_provider

        self.partition_map = {}
        self.public_partition_id_map = {}
        self.partition_id_map = {}
        self.is_mapped = False

        self.partitioner = Partitioner.new(
            table_type, storage_provider, start_sector
        )

        self.table_type = table_type

    def get_device(self):
        """
        Names of partition devices

        Note that the mapping requires an explicit map() call

        :return: instances of MappedDevice

        :rtype: dict
        """
        device_map = {}
        for partition_name, device_node in list(self.partition_map.items()):
            device_map[partition_name] = MappedDevice(
                device=device_node, device_provider=self
            )
        return device_map

    def is_loop(self):
        """
        Check if storage provider is loop based

        The information is taken from the storage provider. If
        the storage provider is loop based the disk is it too

        :return: True or False

        :rtype: bool
        """
        return self.storage_provider.is_loop()

    def create_root_partition(self, mbsize):
        """
        Create root partition

        Populates kiwi_RootPart(id) and kiwi_BootPart(id) if no extra
        boot partition is requested

        :param int mbsize: partition size
        """
        self.partitioner.create('p.lxroot', mbsize, 't.linux')
        self._add_to_map('root')
        self._add_to_public_id_map('kiwi_RootPart')
        if 'kiwi_ROPart' in self.public_partition_id_map:
            self._add_to_public_id_map('kiwi_RWPart')
        if 'kiwi_BootPart' not in self.public_partition_id_map:
            self._add_to_public_id_map('kiwi_BootPart')

    def create_root_lvm_partition(self, mbsize):
        """
        Create root partition for use with LVM

        Populates kiwi_RootPart(id)

        :param int mbsize: partition size
        """
        self.partitioner.create('p.lxlvm', mbsize, 't.lvm')
        self._add_to_map('root')
        self._add_to_public_id_map('kiwi_RootPart')

    def create_root_raid_partition(self, mbsize):
        """
        Create root partition for use with MD Raid

        Populates kiwi_RootPart(id) and kiwi_RaidPart(id) as well
        as the default raid device node at boot time which is
        configured to be kiwi_RaidDev(/dev/mdX)

        :param int mbsize: partition size
        """
        self.partitioner.create('p.lxraid', mbsize, 't.raid')
        self._add_to_map('root')
        self._add_to_public_id_map('kiwi_RootPart')
        self._add_to_public_id_map('kiwi_RaidPart')

    def create_root_readonly_partition(self, mbsize):
        """
        Create root readonly partition for use with overlayfs

        Populates kiwi_ReadOnlyPart(id), the partition is meant to
        contain a squashfs readonly filesystem. The partition size
        should be the size of the squashfs filesystem in order to
        avoid wasting disk space

        :param int mbsize: partition size
        """
        self.partitioner.create('p.lxreadonly', mbsize, 't.linux')
        self._add_to_map('readonly')
        self._add_to_public_id_map('kiwi_ROPart')

    def create_boot_partition(self, mbsize):
        """
        Create boot partition

        Populates kiwi_BootPart(id)

        :param int mbsize: partition size
        """
        self.partitioner.create('p.lxboot', mbsize, 't.linux')
        self._add_to_map('boot')
        self._add_to_public_id_map('kiwi_BootPart')

    def create_prep_partition(self, mbsize):
        """
        Create prep partition

        Populates kiwi_PrepPart(id)

        :param int mbsize: partition size
        """
        self.partitioner.create('p.prep', mbsize, 't.prep')
        self._add_to_map('prep')
        self._add_to_public_id_map('kiwi_PrepPart')

    def create_spare_partition(self, mbsize):
        """
        Create spare partition for custom use

        Populates kiwi_SparePart(id)

        :param int mbsize: partition size
        """
        self.partitioner.create('p.spare', mbsize, 't.linux')
        self._add_to_map('spare')
        self._add_to_public_id_map('kiwi_SparePart')

    def create_swap_partition(self, mbsize):
        """
        Create swap partition

        Populates kiwi_SwapPart(id)

        :param int mbsize: partition size
        """
        self.partitioner.create('p.swap', mbsize, 't.swap')
        self._add_to_map('swap')
        self._add_to_public_id_map('kiwi_SwapPart')

    def create_efi_csm_partition(self, mbsize):
        """
        Create EFI bios grub partition

        Populates kiwi_BiosGrub(id)

        :param int mbsize: partition size
        """
        self.partitioner.create('p.legacy', mbsize, 't.csm')
        self._add_to_map('efi_csm')
        self._add_to_public_id_map('kiwi_BiosGrub')

    def create_efi_partition(self, mbsize):
        """
        Create EFI partition

        Populates kiwi_EfiPart(id)

        :param int mbsize: partition size
        """
        self.partitioner.create('p.UEFI', mbsize, 't.efi')
        self._add_to_map('efi')
        self._add_to_public_id_map('kiwi_EfiPart')

    def activate_boot_partition(self):
        """
        Activate boot partition

        Note: not all Partitioner instances supports this
        """
        partition_id = None
        if 'prep' in self.partition_id_map:
            partition_id = self.partition_id_map['prep']
        elif 'boot' in self.partition_id_map:
            partition_id = self.partition_id_map['boot']
        elif 'root' in self.partition_id_map:
            partition_id = self.partition_id_map['root']

        if partition_id:
            self.partitioner.set_flag(partition_id, 'f.active')

    def create_hybrid_mbr(self):
        """
        Turn partition table into a hybrid GPT/MBR table

        Note: only GPT tables supports this
        """
        self.partitioner.set_hybrid_mbr()

    def create_mbr(self):
        """
        Turn partition table into MBR (msdos table)

        Note: only GPT tables supports this
        """
        self.partitioner.set_mbr()

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
        """
        Map/Activate partitions

        In order to access the partitions through a device node it is
        required to map them if the storage provider is loop based
        """
        if self.storage_provider.is_loop():
            Command.run(
                ['kpartx', '-s', '-a', self.storage_provider.get_device()]
            )
            self.is_mapped = True
        else:
            Command.run(
                ['partprobe', self.storage_provider.get_device()]
            )

    def get_public_partition_id_map(self):
        """
        Populated partition name to number map
        """
        return OrderedDict(
            sorted(self.public_partition_id_map.items())
        )

    def _add_to_public_id_map(self, name, value=None):
        if not value:
            value = self.partitioner.get_id()
        self.public_partition_id_map[name] = value

    def _add_to_map(self, name):
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
            self.partition_id_map[name] = partition_number

    def __del__(self):
        if self.storage_provider.is_loop() and self.is_mapped:
            log.info('Cleaning up %s instance', type(self).__name__)
            try:
                for device_node in self.partition_map.values():
                    Command.run(['dmsetup', 'remove', device_node])
            except Exception:
                log.warning(
                    'cleanup of partition device maps failed, %s still busy',
                    self.storage_provider.get_device()
                )
