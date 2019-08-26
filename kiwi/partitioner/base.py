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


class PartitionerBase:
    """
    **Base class for partitioners**

    :param object disk_provider: Instance of DeviceProvider
    :param int start_sector: sector number
    """
    def __init__(self, disk_provider, start_sector=None):
        self.disk_device = disk_provider.get_device()
        self.partition_id = 0
        self.start_sector = start_sector

        self.flag_map = None

        self.post_init()

    def post_init(self):
        """
        Post initialization method

        Implementation in specialized partitioner class
        """
        pass

    def get_id(self):
        """
        Current partition number

        Zero indicates no partition has been created so far

        :return: partition number

        :rtype: int
        """
        return self.partition_id

    def create(self, name, mbsize, type_name, flags=None):
        """
        Create partition

        Implementation in specialized partitioner class

        :param string name: unused
        :param int mbsize: unused
        :param string type_name: unused
        :param list flags: unused
        """
        raise NotImplementedError

    def set_flag(self, partition_id, flag_name):
        """
        Set partition flag

        Implementation in specialized partitioner class

        :param int partition_id: unused
        :param string flag_name: unused
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

    def resize_table(self, entries=None):
        """
        Resize partition table

        :param int entries: unused
        """
        raise NotImplementedError
