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
from typing import Dict

# project
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.command import Command


class DiskFormatVhdx(DiskFormatBase):
    """
    **Create vhdx image format in dynamic subformat**
    """
    def post_init(self, custom_args: Dict) -> None:
        """
        vhdx disk format post initialization method

        Store qemu options as list from custom args dict

        :param dict custom_args: custom qemu arguments dictionary
        """
        self.image_format = 'vhdx'
        self.options = self.get_qemu_option_list(custom_args)
        self.options.append('-o')
        self.options.append('subformat=dynamic')

    def create_image_format(self) -> None:
        """
        Create vhdx dynamic disk format
        """
        Command.run(
            [
                'qemu-img', 'convert', '-f', 'raw', self.diskname,
                '-O', 'vhdx'
            ] + self.options + [
                self.get_target_file_path_for_format(self.image_format)
            ]
        )
