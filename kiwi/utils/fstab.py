# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from collections import namedtuple

# project
from kiwi.path import Path


class Fstab:
    """
    **Managing fstab values**
    """
    def __init__(self):
        self.fstab = []
        self.fstab_entry_type = namedtuple(
            'fstab_entry_type', [
                'fstype', 'mountpoint', 'device_spec', 'device_path', 'options'
            ]
        )

    def read(self, filename):
        """
        Import specified fstab file

        :param string filename: path to a fstab file
        """
        self.fstab = []
        with open(filename) as fstab:
            for line in fstab.readlines():
                mount_record = line.split()
                if not mount_record or mount_record[0].startswith('#'):
                    continue
                device = mount_record[0]
                mountpoint = mount_record[1]
                fstype = mount_record[2]
                options = mount_record[3]
                if device.startswith('UUID'):
                    device_path = ''.join(
                        ['/dev/disk/by-uuid/', device.split('=')[1]]
                    )
                elif device.startswith('LABEL'):
                    device_path = ''.join(
                        ['/dev/disk/by-label/', device.split('=')[1]]
                    )
                elif device.startswith('PARTUUID'):
                    device_path = ''.join(
                        ['/dev/disk/by-partuuid/', device.split('=')[1]]
                    )
                else:
                    device_path = device

                self.fstab.append(
                    self.fstab_entry_type(
                        fstype=fstype,
                        mountpoint=mountpoint,
                        device_path=device_path,
                        device_spec=device,
                        options=options
                    )
                )

    def get_devices(self):
        return self.fstab

    def export(self, filename):
        """
        Export entries, respect canonical mount order

        :param string filename: path to file name
        """
        fstab_entries_by_path = {}
        for entry in self.fstab:
            fstab_entries_by_path[entry.mountpoint] = entry

        with open(filename, 'w') as fstab:
            for device_path in Path.sort_by_hierarchy(
                sorted(fstab_entries_by_path.keys())
            ):
                entry = fstab_entries_by_path[device_path]
                fstab.write(
                    '{0} {1} {2} {3} 0 0{4}'.format(
                        entry.device_spec, entry.mountpoint,
                        entry.fstype, entry.options,
                        os.linesep
                    )
                )
