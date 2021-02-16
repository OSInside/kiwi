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
from kiwi.command import Command
from kiwi.filesystem.base import FileSystemBase


class FileSystemBtrfs(FileSystemBase):
    """
    **Implements creation of btrfs filesystem**
    """
    def create_on_device(self, label: str = None):
        """
        Create btrfs filesystem on block device

        :param string label: label name
        """
        device = self.device_provider.get_device()
        if label:
            self.custom_args['create_options'].append('-L')
            self.custom_args['create_options'].append(label)
        Command.run(
            ['mkfs.btrfs'] + self.custom_args['create_options'] + [device]
        )
