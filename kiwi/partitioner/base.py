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


class PartitionerBase(object):
    """
        base class for partitioners
    """
    def __init__(self, disk_provider):
        self.disk_device = disk_provider.get_device()
        self.partition_id = 0

        # initial partition type/flag map
        self.flag_map = None

        self.post_init()

    def post_init(self):
        pass

    def get_id(self):
        return self.partition_id

    def create(self, name, mbsize, type_name, flags=None):
        raise NotImplementedError

    def set_flag(self, partition_id, flag_name):
        raise NotImplementedError

    def set_hybrid_mbr(self):
        raise NotImplementedError
