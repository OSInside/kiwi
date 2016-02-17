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
from .command import Command
from .logger import log

from .exceptions import (
    KiwiPartitionerGptFlagError
)


class PartitionerGpt(object):
    """
        implement GPT partition setup
    """
    def __init__(self, disk_provider):
        self.disk_device = disk_provider.get_device()
        self.partition_id = 0

        # gdisk partition type/flag map
        self.flag_map = {
            'f.active': None,
            't.csm': 'EF02',
            't.linux': '8300',
            't.lvm': '8E00',
            't.raid': 'FD00',
            't.efi': 'EF00'
        }

    def get_id(self):
        return self.partition_id

    def create(self, name, mbsize, type_name, flags=None):
        self.partition_id += 1
        if mbsize == 'all_free':
            partition_end = '0'
        else:
            partition_end = '+' + format(mbsize) + 'M'
        Command.run(
            [
                'sgdisk', '-n',
                ':'.join([format(self.partition_id), '0', partition_end]),
                '-c', ':'.join([format(self.partition_id), name]),
                self.disk_device
            ]
        )
        self.set_flag(self.partition_id, type_name)
        if flags:
            for flag_name in flags:
                self.set_flag(self.partition_id, flag_name)

    def set_flag(self, partition_id, flag_name):
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
