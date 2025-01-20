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
import re

# project
from kiwi.command import Command


class BlockID:
    """
    **Get information from a block device**

    :param str device:
        block device node name name. The device can
        also be specified as UUID=<uuid>

    """
    def __init__(self, device):
        uuid_format = re.match(r'^UUID=(.*)', device)
        if uuid_format:
            blkid_result = Command.run(
                ['blkid', '--uuid', uuid_format.group(1)]
            )
            self.device = blkid_result.output.strip(os.linesep)
        else:
            self.device = device

    def get_label(self):
        """
        Retrieve filesystem label from block device

        :return: block device label

        :rtype: str
        """
        return self.get_blkid('LABEL')

    def get_uuid(self):
        """
        Retrieve filesystem uuid from block device

        :return: uuid for the filesystem of the block device

        :rtype: str
        """
        return self.get_blkid('UUID')

    def get_ptuuid(self):
        """
        Retrieve partition uuid from block device

        :return: uuid of the partition table

        :rtype: str
        """
        return self.get_blkid('PTUUID')

    def get_filesystem(self):
        """
        Retrieve filesystem type from block device

        :return: filesystem type

        :rtype: str
        """
        return self.get_blkid('TYPE')

    def get_partition_count(self) -> int:
        """
        Retrieve number of partitions from block device

        :return: A number

        :rtype: int
        """
        partition_count = 0
        lsblk_result = Command.run(
            ['lsblk', '-r', '-o', 'NAME,TYPE', self.device]
        )
        for line in lsblk_result.output.strip().split(os.linesep):
            if line.strip().endswith('part'):
                partition_count += 1
        return partition_count

    def get_blkid(self, id_type):
        """
        Retrieve information for specified metadata ID from block device

        :param string id_type: metadata ID, see man blkid for details

        :return: ID of the block device

        :rtype: str
        """
        blkid_result = Command.run(
            ['blkid', self.device, '-s', id_type, '-o', 'value'],
            raise_on_error=False
        )
        return blkid_result.output.strip(os.linesep) if blkid_result else ''
