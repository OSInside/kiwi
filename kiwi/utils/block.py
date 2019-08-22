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

# project
from kiwi.command import Command


class BlockID:
    """
    **Get information from a block device**

    :param str device: block device node name name

    """
    def __init__(self, device):
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

    def get_filesystem(self):
        """
        Retrieve filesystem type from block device

        :return: filesystem type

        :rtype: str
        """
        return self.get_blkid('TYPE')

    def get_blkid(self, id_type):
        """
        Retrieve information for specified metadata ID from block device

        :param string id_type: metadata ID, see man blkid for details

        :return: ID of the block device

        :rtype: str
        """
        blkid_result = Command.run(
            ['blkid', self.device, '-s', id_type, '-o', 'value']
        )
        return blkid_result.output.strip(os.linesep)
