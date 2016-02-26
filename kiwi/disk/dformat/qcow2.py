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
from .base import DiskFormatBase
from ...command import Command


class DiskFormatQcow2(DiskFormatBase):
    """
        create qcow2 image format
    """
    def post_init(self, custom_args):
        self.options = self.get_qemu_option_list(custom_args)

    def create_image_format(self):
        Command.run(
            [
                'qemu-img', 'convert', '-c', '-f', 'raw', self.diskname,
                '-O', 'qcow2'
            ] + self.options + [
                self.get_target_name_for_format('qcow2')
            ]
        )
