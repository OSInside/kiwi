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
import json
import logging
import re
import shlex
from uuid import UUID
from typing import (
    List, Optional
)

# project
from kiwi.command import Command
from kiwi.partitioner.base import PartitionerBase
from kiwi.utils.temporary import Temporary

from kiwi.exceptions import (
    KiwiPartitionerGptFlagError,
    KiwiDiskGeometryError
)

log = logging.getLogger('kiwi')


class PartitionerGpt(PartitionerBase):
    """
    **Implements GPT partition setup**
    """
    def post_init(self) -> None:
        """
        Post initialization method

        Setup sfdisk GPT partition type/flag map
        """
        self.flag_map = {
            'f.active': None,
            't.csm': 'EF02',
            't.linux': '8300',
            't.swap': '8200',
            't.lvm': '8E00',
            't.raid': 'FD00',
            't.efi': 'EF00',
            't.prep': '4100'
        }
        self.partition_map: dict[int, int] = {}
        self.type_guid_map = {
            'EF02': '21686148-6449-6E6F-744E-656564454649',
            '8300': '0FC63DAF-8483-4772-8E79-3D69D8477DE4',
            '8200': '0657FD6D-A4AB-43C4-84E5-0933C84B4F4F',
            '8E00': 'E6D6D379-F507-44C2-A23C-238F2A3DF928',
            'FD00': 'A19D880F-05FC-4D3B-A006-743F0F84911E',
            'EF00': 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B',
            '4100': '9E1A2D38-C612-4316-AA26-8B49521E5A8B'
        }

    def create(
        self, name: str, mbsize: int, type_name: str, flags: List[str] = None,
        partition_id: Optional[int] = None
    ) -> None:
        """
        Create GPT partition

        :param string name: partition name
        :param int mbsize: partition size
        :param string type_name: partition type
        :param list flags: additional flags
        :param int partition_id:
            If provided, use this exact partition ID
            instead of auto-incrementing
        """
        self.partition_id = \
            partition_id if partition_id else self.partition_id + 1
        self.partition_count += 1
        self.partition_map[self.partition_count] = self.partition_id
        if mbsize == 'all_free':
            partition_size = '+'
        else:
            partition_size = format(mbsize) + 'MiB'
        if self.partition_count > 1 or not self.start_sector:
            # A start sector value of 0 specifies the default value
            # defined in sfdisk
            self.start_sector = 0
        partition_fields = [f'size={partition_size}', f'name={json.dumps(name)}']
        if self.start_sector:
            partition_fields.insert(0, f'start={self.start_sector}')
        self._call_sfdisk(
            [', '.join(partition_fields)],
            ['--force', '-N', format(self.partition_id)]
        )
        self.set_flag(self.partition_id, type_name)
        if flags:
            for flag_name in flags:
                self.set_flag(self.partition_id, flag_name)

    def set_flag(self, partition_id: int, flag_name: str) -> None:
        """
        Set GPT partition flag

        :param int partition_id: partition number
        :param string flag_name: name from flag map
        """
        if flag_name not in self.flag_map:
            raise KiwiPartitionerGptFlagError(
                f'Unknown partition flag {flag_name}'
            )
        if self.flag_map[flag_name]:
            Command.run(
                [
                    'sfdisk', '--part-type', self.disk_device,
                    format(partition_id),
                    self._to_guid(format(self.flag_map[flag_name]))
                ]
            )
        else:
            log.warning('Flag %s ignored on GPT', flag_name)

    def set_uuid(self, partition_id: int, uuid: str) -> None:
        """
        Set partition UUID (TypeCode)

        :param int partition_id: partition number
        :param string uuid: UUID
        """
        Command.run(
            [
                'sfdisk', '--part-uuid', self.disk_device,
                format(partition_id), format(UUID(uuid))
            ]
        )

    def set_hybrid_mbr(self) -> None:
        """
        Turn partition table into hybrid GPT/MBR table
        """
        partition_ids = []
        partition_number_to_embed = self.partition_count
        if partition_number_to_embed > 3:
            # the max number of partitions to embed is 3
            # for details see man sfdisk
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
            if self.partition_map.get(number):
                partition_id = self.partition_map[number]
                start, size = self._get_partition_geometry(partition_id)
                partition_type = self._get_partition_type(partition_id)
                partition_ids.append(
                    '{device}{suffix}{number} : start={start}, '
                    'size={size}, type={type}'.format(
                        device=self.disk_device,
                        suffix='p' if self.disk_device[-1].isdigit() else '',
                        number=number,
                        start=start,
                        size=size,
                        type=self._to_mbr_type(partition_type)
                    )
                )
        self._call_sfdisk(partition_ids, ['--label-nested=mbr'])

    def set_mbr(self) -> None:
        """
        Turn partition table into MBR (msdos table)
        """
        partition_ids = []
        for number in range(1, self.partition_id + 1):
            if self.partition_map.get(number):
                partition_id = self.partition_map[number]
                start, size = self._get_partition_geometry(partition_id)
                partition_type = self._get_partition_type(partition_id)
                partition_ids.append(
                    '{device}{suffix}{number} : start={start}, '
                    'size={size}, type={type}'.format(
                        device=self.disk_device,
                        suffix='p' if self.disk_device[-1].isdigit() else '',
                        number=number,
                        start=start,
                        size=size,
                        type=self._to_mbr_type(partition_type)
                    )
                )
        self._call_sfdisk(['label: dos'] + partition_ids)

    def resize_table(self, entries: int = 128) -> None:
        """
        Resize partition table

        This is done by a dump/reload which automatically corrects
        geometry differences in the table when sfdisk is used

        :param int entries: Specify the maximal number of GPT partitions
        """
        partition_table = Command.run(
            ['sfdisk', '--dump', self.disk_device]
        ).output.splitlines()
        if entries != 128:
            partition_table.insert(0, f'table-length: {entries}')
        self._call_sfdisk(partition_table)

    def _call_sfdisk(
        self, partition_setup: List[str], options: List[str] = None
    ) -> None:
        sfdisk_input = Temporary().new_file()
        with open(sfdisk_input.name, 'w') as partition:
            partition.write('\n'.join(partition_setup) + '\n')
        sfdisk_command = ['sfdisk']
        sfdisk_command.extend(
            [shlex.quote(option) for option in (options or [])]
        )
        sfdisk_command.extend(
            [shlex.quote(self.disk_device), '<', shlex.quote(sfdisk_input.name)]
        )
        command = ' '.join(
            sfdisk_command
        )
        Command.run(['bash', '-c', command])

    def _get_partition_geometry(self, partition_id: int) -> tuple[str, str]:
        partition_info = Command.run(
            ['sfdisk', '--dump', self.disk_device]
        ).output
        partition_node = self._get_partition_node(partition_id)
        partition_match = re.search(
            r'^{partition_node}\s+:\s+start=\s*(\d+), size=\s*(\d+)'.format(
                partition_node=re.escape(partition_node)
            ),
            partition_info,
            re.MULTILINE
        )
        if not partition_match:
            raise KiwiDiskGeometryError(
                f'Failed to locate partition {partition_id}'
            )
        return partition_match.group(1), partition_match.group(2)

    def _get_partition_type(self, partition_id: int) -> str:
        return Command.run(
            ['sfdisk', '--part-type', self.disk_device, format(partition_id)]
        ).output.strip()

    def _to_guid(self, partition_type: str) -> str:
        return self.type_guid_map.get(partition_type, partition_type)

    def _to_mbr_type(self, partition_type: str) -> str:
        partition_type = partition_type.upper()
        if partition_type == self.type_guid_map['8200']:
            return '82'
        if partition_type == self.type_guid_map['8E00']:
            return '8e'
        if partition_type == self.type_guid_map['FD00']:
            return 'fd'
        if partition_type == self.type_guid_map['4100']:
            return '41'
        return '83'

    def _get_partition_node(self, partition_id: int) -> str:
        return ''.join(
            [
                self.disk_device,
                'p' if self.disk_device[-1].isdigit() else '',
                format(partition_id)
            ]
        )
