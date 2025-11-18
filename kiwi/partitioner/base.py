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
from typing import (
    List, Dict, Union
)

# project
from kiwi.storage.device_provider import DeviceProvider


class PartitionerBase:
    """
    **Base class for partitioners**
    """
    def __init__(
        self, disk_provider: DeviceProvider, start_sector: int = None,
        extended_layout: bool = False
    ) -> None:
        """
        Base class constructor for partitioners

        :param object disk_provider: Instance of DeviceProvider
        :param int start_sector: sector number
        :param bool extended_layout:
            If set to true and on msdos table type when creating
            more than 4 partitions, this will cause the fourth
            partition to be an extended partition and all following
            partitions will be placed as logical partitions inside
            of that extended partition
        """
        self.disk_device = disk_provider.get_device()
        self.partition_id = 0
        self.start_sector = start_sector
        self.extended_layout = extended_layout
        self.ec2_layout = False
        self.reserved_ids = set()

        self.flag_map: Dict[str, Union[bool, str, None]] = {}

        self.post_init()

    def post_init(self) -> None:
        """
        Post initialization method

        Implementation in specialized partitioner class
        """
        pass

    def get_id(self) -> int:
        """
        Current partition number

        Zero indicates no partition has been created so far

        :return: partition number

        :rtype: int
        """
        return self.partition_id

    def set_ec2_layout(self, enabled: bool) -> None:
        """
        Enable EC2 layout mode where root partition gets ID 1

        :param bool enabled: Enable EC2 layout
        """
        self.ec2_layout = enabled
        if enabled:
            self.reserved_ids.add(1)  # Reserve partition 1 for root

    def get_next_id(self, is_root: bool = False) -> int:
        """
        Get next partition ID, handling EC2 layout special numbering

        :param bool is_root: True if this is the root partition
        :return: partition ID to use
        :rtype: int
        """
        if self.ec2_layout and is_root:
            # For EC2 root partition, use ID 1 but track the highest ID used
            if self.partition_id == 0:
                self.partition_id = 1
            return 1
        elif self.ec2_layout:
            self.partition_id += 1
            while self.partition_id in self.reserved_ids:
                self.partition_id += 1
            return self.partition_id
        else:
            self.partition_id += 1
            return self.partition_id

    def create(
        self, name: str, mbsize: int, type_name: str, flags: List[str] = []
    ) -> int:
        """
        Create partition

        Implementation in specialized partitioner class

        :param string name: unused
        :param int mbsize: unused
        :param string type_name: unused
        :param list flags: unused
        :return: partition ID that was used
        :rtype: int
        """
        raise NotImplementedError

    def set_flag(self, partition_id: int, flag_name: str):
        """
        Set partition flag

        Implementation in specialized partitioner class

        :param int partition_id: unused
        :param string flag_name: unused
        """
        raise NotImplementedError

    def set_uuid(self, partition_id: int, uuid: str):
        """
        Set partition UUID

        Implementation in specialized partitioner class

        :param int partition_id: unused
        :param string uuid: unused
        """
        raise NotImplementedError

    def set_hybrid_mbr(self):
        """
        Turn partition table into hybrid table if supported

        Implementation in specialized partitioner class
        """
        raise NotImplementedError

    def set_mbr(self):
        """
        Turn partition table into MBR (msdos table)

        Implementation in specialized partitioner class
        """
        raise NotImplementedError

    def set_start_sector(self, start_sector: int):
        """
        Set start sector of first partition as configured

        :param int start_sector: unused

        Does nothing by default
        """
        pass

    def resize_table(self, entries: int = 0):
        """
        Resize partition table

        :param int entries: unused
        """
        raise NotImplementedError
