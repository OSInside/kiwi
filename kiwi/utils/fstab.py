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
import logging
import os
from collections import namedtuple

# project
from kiwi.path import Path

log = logging.getLogger('kiwi')


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

        Read the given fstab file and initialize a new entry list

        :param string filename: path to a fstab file
        """
        self.fstab = []
        with open(filename) as fstab:
            for line in fstab.readlines():
                self.add_entry(line)

    def add_entry(self, line):
        new_entry = self._parse_entry(line)
        if new_entry:
            for entry in self.fstab:
                if entry.mountpoint == new_entry.mountpoint:
                    log.warning(
                        'Mountpoint for "{0}" in use by "{1}", skipped'.format(
                            self._file_entry(new_entry),
                            self._file_entry(entry)
                        )
                    )
                    return
            self.fstab.append(new_entry)

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
                    self._file_entry(entry) + os.linesep
                )

    def _file_entry(self, entry):
        return '{0} {1} {2} {3} 0 0'.format(
            entry.device_spec, entry.mountpoint,
            entry.fstype, entry.options
        )

    def _parse_entry(self, line):
        data_record = line.split()
        if data_record and len(data_record) >= 4 \
           and not data_record[0].startswith('#'):
            device = data_record[0]
            mountpoint = data_record[1]
            fstype = data_record[2]
            options = data_record[3]
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

            return self.fstab_entry_type(
                fstype=fstype,
                mountpoint=mountpoint,
                device_path=device_path,
                device_spec=device,
                options=options
            )
