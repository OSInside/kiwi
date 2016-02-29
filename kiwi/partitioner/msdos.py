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
from ..command import Command
from ..logger import log
from tempfile import NamedTemporaryFile

from ..exceptions import (
    KiwiPartitionerMsDosFlagError
)


class PartitionerMsDos(object):
    """
        implement old style msdos partition setup
    """
    def __init__(self, disk_provider):
        self.disk_device = disk_provider.get_device()
        self.partition_id = 0

        # sfdisk partition type/flag map
        self.flag_map = {
            'f.active': True,
            't.linux': '83',
            't.lvm': '8e',
            't.raid': 'fd',
            't.efi': None,
            't.csm': None,
            't.prep': '41'
        }

    def get_id(self):
        return self.partition_id

    def create(self, name, mbsize, type_name, flags=None):
        self.partition_id += 1
        fdisk_input = NamedTemporaryFile()
        with open(fdisk_input.name, 'w') as partition:
            log.debug(
                '%s: fdisk: n p %d cur_position +%sM w q',
                name, self.partition_id, format(mbsize)
            )
            if mbsize == 'all_free':
                partition.write(
                    'n\np\n%d\n\n\nw\nq\n' % self.partition_id
                )
            else:
                partition.write(
                    'n\np\n%d\n\n+%dM\nw\nq\n' %
                    (self.partition_id, mbsize)
                )
        bash_command = ' '.join(
            ['cat', fdisk_input.name, '|', 'fdisk', self.disk_device]
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

        self.set_flag(self.partition_id, type_name)
        if flags:
            for flag_name in flags:
                self.set_flag(self.partition_id, flag_name)

    def set_flag(self, partition_id, flag_name):
        if flag_name not in self.flag_map:
            raise KiwiPartitionerMsDosFlagError(
                'Unknown partition flag %s' % flag_name
            )
        if self.flag_map[flag_name]:
            if flag_name == 'f.active':
                Command.run(
                    [
                        'sfdisk', '--activate=' + format(partition_id),
                        self.disk_device
                    ]
                )
            else:
                Command.run(
                    [
                        'sfdisk', '-c', self.disk_device,
                        format(partition_id), self.flag_map[flag_name]
                    ]
                )
        else:
            log.warning('Flag %s ignored on msdos', flag_name)
