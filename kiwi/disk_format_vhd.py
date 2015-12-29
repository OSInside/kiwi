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
from command import Command
from disk_format_base import DiskFormatBase
from collections import OrderedDict


class DiskFormatVhd(DiskFormatBase):
    """
        create vhd image format
    """
    def post_init(self, custom_args):
        self.options = []
        if custom_args:
            self.options.append('-o')
            ordered_args = OrderedDict(custom_args.items())
            for key, value in custom_args.iteritems():
                self.options.append(key)
                self.options.append(value)

    def create_image_format(self):
        Command.run(
            [
                'qemu-img', 'convert', '-c', '-f', 'raw', self.diskname,
                '-O', 'vpc'
            ] + self.options + [
                self.get_target_name_for_format('vhd')
            ]
        )
