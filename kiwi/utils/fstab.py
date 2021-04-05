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
from typing import (
    NamedTuple, List
)
import logging
import os

# project
from kiwi.path import Path

log = logging.getLogger('kiwi')

fstab_entry_type = NamedTuple(
    'fstab_entry_type', [
        ('fstype', str),
        ('mountpoint', str),
        ('device_spec', str),
        ('device_path', str),
        ('options', str),
        ('dump', str),
        ('fs_passno', str)
    ]
)


class Fstab:
    """
    **Managing fstab values**
    """
    def __init__(self):
        self.fstab = []

    def read(self, filename: str) -> None:
        """
        Import specified fstab file

        Read the given fstab file and initialize a new entry list

        :param string filename: path to a fstab file
        """
        self.fstab = []
        with open(filename) as fstab:
            for line in fstab.readlines():
                self.add_entry(line)

    def add_entry(self, line: str) -> None:
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

    def get_devices(self) -> List[fstab_entry_type]:
        return self.fstab

    def export(self, filename: str) -> None:
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
        return '{0} {1} {2} {3} {4} {5}'.format(
            entry.device_spec, entry.mountpoint,
            entry.fstype, entry.options, entry.dump,
            entry.fs_passno
        )

    def _parse_entry(self, line):
        data_record = line.split()
        if data_record and len(data_record) >= 6 \
           and not data_record[0].startswith('#'):
            device = data_record[0]
            mountpoint = data_record[1]
            fstype = data_record[2]
            options = data_record[3]
            dump = data_record[4]
            fs_passno = data_record[5]
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

            return fstab_entry_type(
                fstype=fstype,
                mountpoint=mountpoint,
                device_path=device_path,
                device_spec=device,
                options=options,
                dump=dump,
                fs_passno=fs_passno
            )
