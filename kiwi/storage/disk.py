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
from typing import (
    Dict, NamedTuple, Tuple
)

# project
from kiwi.defaults import Defaults
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.storage.device_provider import DeviceProvider
from kiwi.storage.mapped_device import MappedDevice
from kiwi.partitioner import Partitioner
from kiwi.runtime_config import RuntimeConfig
from kiwi.exceptions import (
    KiwiCustomPartitionConflictError,
    KiwiError
)

ptable_entry_type = NamedTuple(
    'ptable_entry_type', [
        ('mbsize', int),
        ('clone', int),
        ('partition_name', str),
        ('partition_type', str),
        ('mountpoint', str),
        ('filesystem', str)
    ]
)

log = logging.getLogger('kiwi')


class Disk(DeviceProvider):
    """
    **Implements storage disk and partition table setup**
    """
    def __init__(
        self, table_type: str, storage_provider: DeviceProvider,
        start_sector: int = None, extended_layout: bool = False
    ):
        """
        Construct a new Disk layout object

        :param string table_type: Partition table type name
        :param object storage_provider:
            Instance of class based on DeviceProvider
        :param int start_sector: sector number
        :param bool extended_layout:
            If set to true and on msdos table type when creating
            more than 4 partitions, this will cause the fourth
            partition to be an extended partition and all following
            partitions will be placed as logical partitions inside
            of that extended partition
        """
        self.partition_mapper = RuntimeConfig().get_mapper_tool()
        #: the underlaying device provider
        self.storage_provider = storage_provider

        #: list of protected map ids. If used in a custom partitions
        #: setup this will lead to a raise conditition in order to
        #: avoid conflicts with the existing partition layout and its
        #: customizaton capabilities
        self.protected_map_ids = [
            'root',
            'readonly',
            'boot',
            'prep',
            'spare',
            'swap',
            'efi_csm',
            'efi'
        ]

        #: Unified partition UUIDs according to systemd
        self.gUID = self.get_discoverable_partition_ids()

        self.partition_map: Dict[str, str] = {}
        self.public_partition_id_map: Dict[str, str] = {}
        self.partition_id_map: Dict[str, str] = {}
        self.is_mapped = False

        self.partitioner = Partitioner.new(
            table_type, storage_provider, start_sector, extended_layout
        )

        self.table_type = table_type

    def __enter__(self):
        return self

    def get_device(self) -> Dict[str, MappedDevice]:
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

    def is_loop(self) -> bool:
        """
        Check if storage provider is loop based

        The information is taken from the storage provider. If
        the storage provider is loop based the disk is it too

        :return: True or False

        :rtype: bool
        """
        return self.storage_provider.is_loop()

    def create_custom_partitions(
        self, table_entries: Dict[str, ptable_entry_type]
    ) -> None:
        """
        Create partitions from custom data set

        .. code:: python

           table_entries = {
               map_name: ptable_entry_type
           }

        :param dict table: partition table spec
        """
        for map_name in table_entries:
            if map_name in self.protected_map_ids:
                raise KiwiCustomPartitionConflictError(
                    f'Cannot use reserved table entry name: {map_name!r}'
                )
            entry = table_entries[map_name]
            if entry.clone:
                self._create_clones(
                    map_name, entry.clone, entry.partition_type,
                    format(entry.mbsize)
                )
            id_name = f'kiwi_{map_name.title()}Part'
            self.partitioner.create(
                entry.partition_name, entry.mbsize, entry.partition_type
            )
            self._add_to_map(map_name)
            self._add_to_public_id_map(id_name)
            part_uuid = self.gUID.get(entry.partition_name)
            if part_uuid:
                self.partitioner.set_uuid(
                    self.partition_id_map[map_name], part_uuid
                )

    def create_root_partition(self, mbsize: str, clone: int = 0):
        """
        Create root partition

        Populates kiwi_RootPart(id) and kiwi_BootPart(id) if no extra
        boot partition is requested

        :param str mbsize: partition size string
        :param int clone: create [clone] cop(y/ies) of the root partition
        """
        (mbsize, mbsize_clone) = Disk._parse_size(mbsize)
        if clone:
            self._create_clones('root', clone, 't.linux', mbsize_clone)
        self.partitioner.create('p.lxroot', mbsize, 't.linux')
        self._add_to_map('root')
        self._add_to_public_id_map('kiwi_RootPart')
        if 'kiwi_ROPart' in self.public_partition_id_map:
            self._add_to_public_id_map('kiwi_RWPart')
        if 'kiwi_BootPart' not in self.public_partition_id_map:
            self._add_to_public_id_map('kiwi_BootPart')
        root_uuid = self.gUID.get('root')
        if root_uuid:
            self.partitioner.set_uuid(
                self.partition_id_map['root'], root_uuid
            )

    def create_root_lvm_partition(self, mbsize: str, clone: int = 0):
        """
        Create root partition for use with LVM

        Populates kiwi_RootPart(id)

        :param str mbsize: partition size string
        :param int clone: create [clone] cop(y/ies) of the lvm roo partition
        """
        (mbsize, mbsize_clone) = Disk._parse_size(mbsize)
        if clone:
            self._create_clones('root', clone, 't.lvm', mbsize_clone)
        self.partitioner.create('p.lxlvm', mbsize, 't.lvm')
        self._add_to_map('root')
        self._add_to_public_id_map('kiwi_RootPart')
        root_uuid = self.gUID.get('root')
        if root_uuid:
            self.partitioner.set_uuid(
                self.partition_id_map['root'], root_uuid
            )

    def create_root_raid_partition(self, mbsize: str, clone: int = 0):
        """
        Create root partition for use with MD Raid

        Populates kiwi_RootPart(id) and kiwi_RaidPart(id) as well
        as the default raid device node at boot time which is
        configured to be kiwi_RaidDev(/dev/mdX)

        :param str mbsize: partition size string
        :param int clone: create [clone] cop(y/ies) of the raid root partition
        """
        (mbsize, mbsize_clone) = Disk._parse_size(mbsize)
        if clone:
            self._create_clones('root', clone, 't.raid', mbsize_clone)
        self.partitioner.create('p.lxraid', mbsize, 't.raid')
        self._add_to_map('root')
        self._add_to_public_id_map('kiwi_RootPart')
        self._add_to_public_id_map('kiwi_RaidPart')
        root_uuid = self.gUID.get('root')
        if root_uuid:
            self.partitioner.set_uuid(
                self.partition_id_map['root'], root_uuid
            )

    def create_root_readonly_partition(self, mbsize: str, clone: int = 0):
        """
        Create root readonly partition for use with overlayfs

        Populates kiwi_ReadOnlyPart(id), the partition is meant to
        contain a squashfs readonly filesystem. The partition size
        should be the size of the squashfs filesystem in order to
        avoid wasting disk space

        :param str mbsize: partition size string
        :param int clone: create [clone] cop(y/ies) of the ro root partition
        """
        (mbsize, mbsize_clone) = Disk._parse_size(mbsize)
        if clone:
            self._create_clones('root', clone, 't.linux', mbsize_clone)
        self.partitioner.create('p.lxreadonly', mbsize, 't.linux')
        self._add_to_map('readonly')
        self._add_to_public_id_map('kiwi_ROPart')
        root_uuid = self.gUID.get('root')
        if root_uuid:
            self.partitioner.set_uuid(
                self.partition_id_map['readonly'], root_uuid
            )

    def create_boot_partition(self, mbsize: str, clone: int = 0):
        """
        Create boot partition

        Populates kiwi_BootPart(id) and optional kiwi_BootPartClone(id)

        :param str mbsize: partition size string
        :param int clone: create [clone] cop(y/ies) of the boot partition
        """
        (mbsize, mbsize_clone) = Disk._parse_size(mbsize)
        if clone:
            self._create_clones('boot', clone, 't.linux', mbsize_clone)
        self.partitioner.create('p.lxboot', mbsize, 't.linux')
        self._add_to_map('boot')
        self._add_to_public_id_map('kiwi_BootPart')
        boot_uuid = self.gUID.get('xbootldr')
        if boot_uuid:
            self.partitioner.set_uuid(
                self.partition_id_map['boot'], boot_uuid
            )

    def create_prep_partition(self, mbsize: str):
        """
        Create prep partition

        Populates kiwi_PrepPart(id)

        :param str mbsize: partition size string
        """
        (mbsize, _) = Disk._parse_size(mbsize)
        self.partitioner.create('p.prep', mbsize, 't.prep')
        self._add_to_map('prep')
        self._add_to_public_id_map('kiwi_PrepPart')

    def create_spare_partition(self, mbsize: str):
        """
        Create spare partition for custom use

        Populates kiwi_SparePart(id)

        :param str mbsize: partition size string
        """
        (mbsize, _) = Disk._parse_size(mbsize)
        self.partitioner.create('p.spare', mbsize, 't.linux')
        self._add_to_map('spare')
        self._add_to_public_id_map('kiwi_SparePart')

    def create_swap_partition(self, mbsize: str):
        """
        Create swap partition

        Populates kiwi_SwapPart(id)

        :param str mbsize: partition size string
        """
        (mbsize, _) = Disk._parse_size(mbsize)
        self.partitioner.create('p.swap', mbsize, 't.swap')
        self._add_to_map('swap')
        self._add_to_public_id_map('kiwi_SwapPart')
        swap_uuid = self.gUID.get('swap')
        if swap_uuid:
            self.partitioner.set_uuid(
                self.partition_id_map['swap'], swap_uuid
            )

    def create_efi_csm_partition(self, mbsize: str):
        """
        Create EFI bios grub partition

        Populates kiwi_BiosGrub(id)

        :param str mbsize: partition size string
        """
        (mbsize, _) = Disk._parse_size(mbsize)
        self.partitioner.create('p.legacy', mbsize, 't.csm')
        self._add_to_map('efi_csm')
        self._add_to_public_id_map('kiwi_BiosGrub')

    def create_efi_partition(self, mbsize: str):
        """
        Create EFI partition

        Populates kiwi_EfiPart(id)

        :param str mbsize: partition size string
        """
        (mbsize, _) = Disk._parse_size(mbsize)
        self.partitioner.create('p.UEFI', mbsize, 't.efi')
        self._add_to_map('efi')
        self._add_to_public_id_map('kiwi_EfiPart')
        esp_uuid = self.gUID.get('esp')
        if esp_uuid:
            self.partitioner.set_uuid(
                self.partition_id_map['efi'], esp_uuid
            )

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

    def set_start_sector(self, start_sector: int):
        """
        Set start sector

        Note: only effective on DOS tables
        """
        self.partitioner.set_start_sector(start_sector)

    def wipe(self):
        """
        Zap (destroy) any GPT and MBR data structures if present
        For DASD disks create a new VTOC table
        """
        if 'dasd' in self.table_type:
            log.debug('Initialize DASD disk with new VTOC table')
            fdasd_input = Temporary().new_file()
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
            if self.partition_mapper == 'kpartx':
                Command.run(
                    ['kpartx', '-s', '-a', self.storage_provider.get_device()]
                )
            else:
                Command.run(
                    ['partx', '--add', self.storage_provider.get_device()]
                )
            self.is_mapped = True
        else:
            Command.run(
                ['partprobe', self.storage_provider.get_device()]
            )

    def get_public_partition_id_map(self) -> Dict[str, str]:
        """
        Populated partition name to number map
        """
        return OrderedDict(
            sorted(self.public_partition_id_map.items())
        )

    def get_discoverable_partition_ids(self) -> Dict[str, str]:
        """
        Ask systemd for a list of standardized GUIDs for the
        current architecture and return them in a dictionary.
        If there is no such information available an empty
        dictionary is returned

        :return: key:value dict from systemd-id128

        :rtype: dict
        """
        discoverable_ids = {}
        try:
            raw_lines = Command.run(
                ['systemd-id128', 'show']
            ).output.split(os.linesep)[1:]
            for line in raw_lines:
                if line:
                    line = ' '.join(line.split())
                    partition_name, uuid = line.split(' ')
                    discoverable_ids[partition_name] = uuid
        except KiwiError as issue:
            log.warning(
                f'Failed to obtain discoverable partition IDs: {issue}'
            )
            log.warning(
                'Using built-in table'
            )
            discoverable_ids = Defaults.get_discoverable_partition_ids()
        return discoverable_ids

    def _create_clones(
        self, name: str, clone: int, type_flag: str, mbsize: str
    ) -> None:
        """
        Create [clone] cop(y/ies) of the given partition name

        The name of a clone partition uses the following name policy:

        * {name}clone{id} for the partition name
        * kiwi_{name}PartClone{id} for the kiwi map name

        :param str name: basename to use for clone partition names
        :param int clone: number of clones, >= 1
        :param str type_flag: partition type name
        :param str mbsize: partition size string
        """
        for clone_id in range(1, clone + 1):
            self.partitioner.create(
                f'p.lx{name}clone{clone_id}', mbsize, type_flag
            )
            self._add_to_map(f'{name}clone{clone_id}')
            self._add_to_public_id_map(f'kiwi_{name}PartClone{clone_id}')

    @staticmethod
    def _parse_size(value: str) -> Tuple[str, str]:
        """
        parse size value. This can be one of the following

        * A number_string
        * The string named: 'all_free'
        * The string formatted as:
              clone:{number_string_origin}:{number_string_clone}

        The method returns a tuple for size and optional clone size
        If no clone size exists both tuple values are the same

        The given number_string for the size of the partition is
        passed along to the actually used partitioner object and
        expected to be valid there. In case invalid size information
        is passed to the partitioner an exception will be raised
        in the scope of the partitioner interface and the selected
        partitioner class

        :param str value: size value

        :return: Tuple of strings

        :rtype: tuple
        """
        if not format(value).startswith('clone:'):
            return (value, value)
        else:
            size_list = value.split(':')
            return (size_list[1], size_list[2])

    def _add_to_public_id_map(self, name, value=None):
        if not value:
            value = self.partitioner.get_id()
        self.public_partition_id_map[name] = value

    def _add_to_map(self, name):
        device_node = None
        partition_number = format(self.partitioner.get_id())
        if self.storage_provider.is_loop():
            device_base = os.path.basename(self.storage_provider.get_device())
            if self.partition_mapper == 'kpartx':
                device_node = ''.join(
                    ['/dev/mapper/', device_base, 'p', partition_number]
                )
            else:
                device_node = ''.join(
                    ['/dev/', device_base, 'p', partition_number]
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

    def __exit__(self, exc_type, exc_value, traceback):
        if self.storage_provider.is_loop() and self.is_mapped:
            log.info('Cleaning up %s instance', type(self).__name__)
            try:
                if self.partition_mapper == 'kpartx':
                    for device_node in self.partition_map.values():
                        Command.run(['dmsetup', 'remove', device_node])
                    Command.run(
                        ['kpartx', '-d', self.storage_provider.get_device()]
                    )
                else:
                    Command.run(
                        ['partx', '--delete', self.storage_provider.get_device()]
                    )
            except Exception as issue:
                log.error(
                    'cleanup of partition maps on {} failed with: {}'.format(
                        self.storage_provider.get_device(), issue
                    )
                )
