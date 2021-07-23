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
from kiwi.utils.temporary import Temporary
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.command import Command
from kiwi.system.result import Result


class DiskFormatQcow2(DiskFormatBase):
    """
    **Create qcow2 disk format**
    """
    def post_init(self, custom_args: dict) -> None:
        """
        qcow2 disk format post initialization method

        Store qemu options as list from custom args dict

        :param dict custom_args: custom qemu arguments dictionary
        """
        self.image_format: str = 'qcow2'
        self.options = self.get_qemu_option_list(custom_args)

    def create_image_format(self) -> None:
        """
        Create qcow2 disk format
        """
        intermediate = Temporary().new_file()
        Command.run(
            [
                'qemu-img', 'convert', '-f', 'raw', self.diskname,
                '-O', self.image_format
            ] + self.options + [
                intermediate.name
            ]
        )
        Command.run(
            [
                'qemu-img', 'convert', '-c', '-f', self.image_format,
                intermediate.name, '-O', self.image_format,
                self.get_target_file_path_for_format(self.image_format)
            ]
        )

    def store_to_result(self, result: Result) -> None:
        """
        Store result file of the format conversion into the
        provided result instance.

        In case of a qcow2 format we store the result uncompressed
        Since the format conversion only takes the real bytes into
        account such that the sparseness of the raw disk will not
        result in the output format and can be taken one by one

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.get_target_file_path_for_format(
                self.image_format
            ),
            use_for_bundle=True,
            compress=self.runtime_config.get_bundle_compression(
                default=False
            ),
            shasum=True
        )
