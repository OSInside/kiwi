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
import logging
from typing import List

# project
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.partitioner.base import PartitionerBase
from kiwi.utils.block import BlockID

from kiwi.exceptions import (
    KiwiPartitionerMsDosFlagError
)

log = logging.getLogger('kiwi')


class PartitionerMsDos(PartitionerBase):
    """
    **Implement old style msdos partition setup**
    """
    def post_init(self) -> None:
        """
        Post initialization method

        Setup sfdisk partition type/flag map
        """
        self.default_start = 2048
        self.sector_size = 512
        self.flag_map = {
            'f.active': True,
            't.linux': '83',
            't.swap': '82',
            't.lvm': '8e',
            't.raid': 'fd',
            't.efi': None,
            't.csm': None,
            't.prep': '41',
            't.extended': '5'
        }

    def create(
        self, name: str, mbsize: int, type_name: str, flags: List[str] = []
    ) -> None:
        """
        Create msdos partition

        :param string name: partition name
        :param int mbsize: partition size
        :param string type_name: partition type
        :param list flags: additional flags
        """
        if self.extended_layout:
            if self.partition_id < 3:
                # in primary boundary
                self._create_primary(name, mbsize, type_name, flags)
            elif self.partition_id == 3:
                # at primary boundary, create extended + logical
                self._create_extended(name)
                self._create_logical(name, mbsize, type_name, flags)
            elif self.partition_id > 3:
                # in logical boundary
                self._create_logical(name, mbsize, type_name, flags)
        else:
            self._create_primary(name, mbsize, type_name, flags)

    def set_flag(self, partition_id: int, flag_name: str) -> None:
        """
        Set msdos partition flag

        :param int partition_id: partition number
        :param string flag_name: name from flag map
        """
        if flag_name not in self.flag_map:
            raise KiwiPartitionerMsDosFlagError(
                'Unknown partition flag %s' % flag_name
            )
        flag_val = self.flag_map[flag_name]
        if flag_val:
            if flag_name == 'f.active':
                Command.run(
                    [
                        'parted', self.disk_device,
                        'set', format(partition_id), 'boot', 'on'
                    ]
                )
            else:
                assert isinstance(flag_val, str), f"flag {flag_name} must be a string but got a {type(flag_val)}"
                Command.run(
                    [
                        'sfdisk', '-c', self.disk_device,
                        format(partition_id), flag_val
                    ]
                )
        else:
            log.warning('Flag %s ignored on msdos', flag_name)

    def resize_table(self, entries: int = None) -> None:
        """
        Resize partition table

        Nothing to be done here for msdos table

        :param int entries: unused
        """
        pass

    def set_uuid(self, partition_id: int, uuid: str) -> None:
        """
        Set partition UUID

        Nothing to be done here for MSDOS devices

        :param int partition_id: unused
        :param string uuid: unused
        """
        pass  # pragma: nocover

    def set_start_sector(self, start_sector: int):
        """
        Set start sector of first partition as configured.
        fdisk and friends are not able to work correctly if
        the start sector of the first partition is any different
        from 2048.

        :param int start_sector: sector size
        """
        block_operation = BlockID(self.disk_device)
        fdisk_input = Temporary().new_file()
        with open(fdisk_input.name, 'w') as partition:
            if block_operation.get_partition_count() >= 4:
                # if the partition table is full fdisk does not ask
                # for the partition number when there is only one choice
                log.debug(f'fdisk: d 1 n p {start_sector} w q')
                partition.write(
                    'd\n1\nn\np\n{0}\n\nw\nq\n'.format(start_sector)
                )
            else:
                # if the partition table has less than 4 partitions
                # fdisk will ask for the partition number to change
                log.debug(f'fdisk: d 1 n p 1 {start_sector} w q')
                partition.write(
                    'd\n1\nn\np\n1\n{0}\n\nw\nq\n'.format(start_sector)
                )
        self._call_fdisk(fdisk_input.name)

    def _create_primary(
        self, name: str, mbsize: int, type_name: str, flags: List[str] = []
    ) -> None:
        """
        Create primary msdos partition
        """
        self.partition_id += 1
        fdisk_input = Temporary().new_file()
        if self.partition_id == 1 and self.start_sector:
            if self.start_sector > self.default_start and mbsize != 'all_free':
                # fdisk default start sector is self.default_start, increase
                # the partition size such that after set_start_sector()
                # the requested partition size is present
                mbsize += int(
                    (self.start_sector - self.default_start) * self.sector_size / (1024 * 1024)
                )
        with open(fdisk_input.name, 'w') as partition:
            log.debug(
                '%s: fdisk: n p %d cur_position +%sM w q',
                name, self.partition_id, format(mbsize)
            )
            partition.write(
                'n\np\n{0}\n\n{1}\nw\nq\n'.format(
                    self.partition_id,
                    '' if mbsize == 'all_free' else '+{0}M'.format(mbsize)
                )
            )
        self._call_fdisk(fdisk_input.name)
        self._set_all_flags(type_name, flags)

    def _create_extended(self, name: str) -> None:
        """
        Create extended msdos partition
        """
        self.partition_id += 1
        fdisk_input = Temporary().new_file()
        with open(fdisk_input.name, 'w') as partition:
            log.debug(
                '%s: fdisk: n e %d cur_position +all_freeM w q',
                name, self.partition_id
            )
            partition.write(
                'n\ne\n{0}\n{1}\n{2}\nw\nq\n'.format(
                    self.partition_id, '', ''
                )
            )
        self._call_fdisk(fdisk_input.name)

    def _create_logical(
        self, name: str, mbsize: int, type_name: str, flags: List[str] = []
    ) -> None:
        """
        Create logical msdos partition
        """
        self.partition_id += 1
        fdisk_input = Temporary().new_file()
        with open(fdisk_input.name, 'w') as partition:
            log.debug(
                '%s: fdisk: n %d cur_position +%sM w q',
                name, self.partition_id, format(mbsize)
            )
            partition.write(
                'n\n{0}\n{1}\n{2}\nw\nq\n'.format(
                    self.partition_id,
                    '',
                    '' if mbsize == 'all_free' else '+{0}M'.format(mbsize)
                )
            )
        self._call_fdisk(fdisk_input.name)
        self._set_all_flags(type_name, flags)

    def _set_all_flags(self, type_name: str, flags: List[str]) -> None:
        self.set_flag(self.partition_id, type_name)
        if flags:
            for flag_name in flags:
                self.set_flag(self.partition_id, flag_name)

    def _call_fdisk(self, fdisk_config_file_path: str) -> None:
        bash_command = ' '.join(
            ['cat', fdisk_config_file_path, '|', 'fdisk', self.disk_device]
        )
        try:
            Command.run(
                ['bash', '-c', bash_command]
            )
        except Exception:
            # unfortunately fdisk reports that it can't read in the partition
            # table which I consider a bug in fdisk. However the table was
            # correctly created and therefore we continue. Problem is that we
            # are not able to detect real errors with the fdisk operation at
            # that point.
            log.debug('potential fdisk errors were ignored')
