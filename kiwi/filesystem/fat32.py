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

# project
import kiwi.defaults as defaults

from kiwi.filesystem.base import FileSystemBase
from kiwi.command import Command


class FileSystemFat32(FileSystemBase):
    """
    **Implements creation of fat32 filesystem**
    """
    def create_on_device(
        self, label: str = None, size: int = 0, unit: str = defaults.UNIT.kb,
        uuid: str = None
    ):
        """
        Create fat32 filesystem on block device

        :param str label: label name
        :param int size:
            size value, can also be counted from the end via -X
            The value is interpreted in units of: unit
        :param str unit:
            unit name. Default unit is set to: defaults.UNIT.kb
        :param str uuid: Volume Label, there is no real UUID on fat
        """
        device_args = [self.device_provider.get_device()]
        if label:
            self.custom_args['create_options'].append('-n')
            self.custom_args['create_options'].append(label)
        if uuid:
            self.custom_args['create_options'].append('-i')
            self.custom_args['create_options'].append(uuid)
        if size:
            device_args.append(
                self._fs_size(
                    size=self._map_size(
                        size, from_unit=unit, to_unit=defaults.UNIT.kb
                    ), unit=defaults.UNIT.kb
                )
            )
        Command.run(
            [
                'mkdosfs', '-F32', '-I'
            ] + self.custom_args['create_options'] + device_args
        )

    def set_uuid(self):
        """
        Create new random filesystem UUID
        """
        device = self.device_provider.get_device()
        Command.run(
            ['mlabel', '-n', '-i', device, '::']
        )
