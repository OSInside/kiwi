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
from kiwi.command import Command
from kiwi.logger import log
from kiwi.partitioner.base import PartitionerBase

from kiwi.exceptions import (
    KiwiPartitionerGptFlagError
)


class PartitionerGpt(PartitionerBase):
    """
    **Implements GPT partition setup**
    """
    def post_init(self):
        """
        Post initialization method

        Setup gdisk partition type/flag map
        """
        self.flag_map = {
            'f.active': None,
            't.csm': 'EF02',
            't.linux': '8300',
            't.lvm': '8E00',
            't.raid': 'FD00',
            't.efi': 'EF00'
        }

    def create(self, name, mbsize, type_name, flags=None):
        """
        Create GPT partition

        :param string name: partition name
        :param int mbsize: partition size
        :param string type_name: partition type
        :param list flags: additional flags
        """
        self.partition_id += 1
        if mbsize == 'all_free':
            partition_end = '0'
        else:
            partition_end = '+' + format(mbsize) + 'M'
        if self.partition_id > 1 or not self.start_sector:
            # A start  sector value of 0 specifies the default value
            # defined in sgdisk
            self.start_sector = 0
        Command.run(
            [
                'sgdisk', '-n', ':'.join(
                    [
                        format(self.partition_id),
                        format(self.start_sector),
                        partition_end
                    ]
                ), '-c', ':'.join([format(self.partition_id), name]),
                self.disk_device
            ]
        )
        self.set_flag(self.partition_id, type_name)
        if flags:
            for flag_name in flags:
                self.set_flag(self.partition_id, flag_name)

    def set_flag(self, partition_id, flag_name):
        """
        Set GPT partition flag

        :param int partition_id: partition number
        :param string flag_name: name from flag map
        """
        if flag_name not in self.flag_map:
            raise KiwiPartitionerGptFlagError(
                'Unknown partition flag %s' % flag_name
            )
        if self.flag_map[flag_name]:
            Command.run(
                [
                    'sgdisk', '-t',
                    ':'.join([format(partition_id), self.flag_map[flag_name]]),
                    self.disk_device
                ]
            )
        else:
            log.warning('Flag %s ignored on GPT', flag_name)

    def set_hybrid_mbr(self):
        """
        Turn partition table into hybrid GPT/MBR table
        """
        partition_ids = []
        partition_number_to_embed = self.partition_id
        if partition_number_to_embed > 3:
            # the max number of partitions to embed is 3
            # for details see man sgdisk
            log.debug(
                'maximum number of GPT hybrid MBR partitions is 3, got %d',
                partition_number_to_embed
            )
            partition_number_to_embed = 3
            log.debug(
                'reduced GPT hybrid MBR partition count to %d',
                partition_number_to_embed
            )
        for number in range(1, partition_number_to_embed + 1):
            partition_ids.append(format(number))
        Command.run(
            ['sgdisk', '-h', ':'.join(partition_ids), self.disk_device]
        )

    def set_mbr(self):
        """
        Turn partition table into MBR (msdos table)
        """
        partition_ids = []
        efi_partition_number = None
        for number in range(1, self.partition_id + 1):
            partition_info = Command.run(
                ['sgdisk', '-i={0}'.format(number), self.disk_device]
            )
            if '(EFI System)' in partition_info.output:
                efi_partition_number = number
            partition_ids.append(format(number))
        Command.run(
            ['sgdisk', '-m', ':'.join(partition_ids), self.disk_device]
        )
        if efi_partition_number:
            # turn former EFI partition into standard linux partition
            self.set_flag(efi_partition_number, 't.linux')

    def resize_table(self, entries=128):
        """
        Resize partition table

        :param int entries: number of default entries
        """
        Command.run(
            [
                'sgdisk', '--resize-table', '{0}'.format(entries),
                self.disk_device
            ]
        )
