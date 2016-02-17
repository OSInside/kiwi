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
from tempfile import NamedTemporaryFile


class PartitionerDasd(object):
    """
        implement fdasd partition setup
    """
    def __init__(self, disk_provider):
        self.disk_device = disk_provider.get_device()
        self.partition_id = 0

        # fdasd partition type/flag map
        self.flag_map = {
            'f.active': None,
            't.linux': '1',
            't.lvm': '1',
            't.raid': '1',
            't.efi': None,
            't.csm': None
        }

    def get_id(self):
        return self.partition_id

    def create(self, name, mbsize, type_name, flags=None):
        self.partition_id += 1
        fdasd_input = NamedTemporaryFile()
        with open(fdasd_input.name, 'w') as partition:
            log.debug(
                '%s: fdasd: n p cur_position +%sM w q',
                name, format(mbsize)
            )
            if mbsize == 'all_free':
                partition.write('n\np\n\n\nw\nq\n')
            else:
                partition.write('n\np\n\n+%dM\nw\nq\n' % mbsize)
        bash_command = ' '.join(
            ['cat', fdasd_input.name, '|', 'fdasd', '-f', self.disk_device]
        )
        Command.run(
            ['bash', '-c', bash_command]
        )

    def set_flag(self, partition_id, flag_name):
        # on an s390 dasd device there are no such flags
        pass
