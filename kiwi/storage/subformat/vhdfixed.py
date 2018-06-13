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
import struct
from binascii import unhexlify
import re

# project
from kiwi.storage.subformat.base import DiskFormatBase
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiVhdTagError
)


class DiskFormatVhdFixed(DiskFormatBase):
    """
    **Create vhd image format in fixed subformat**
    """
    def post_init(self, custom_args):
        """
        vhd disk format post initialization method

        Store qemu options as list from custom args dict
        Extract disk tag from custom args

        :param dict custom_args:
            custom vhdfixed and qemu argument dictionary

            .. code:: python

                {'--tag': 'billing_code', '--qemu-opt': 'value'}
        """
        self.image_format = 'vhdfixed'
        self.tag = None
        if '--tag' in custom_args:
            self.tag = custom_args['--tag']
            del custom_args['--tag']

        self.options = self.get_qemu_option_list(custom_args)
        self.options.append('-o')
        self.options.append('subformat=fixed')

    def create_image_format(self):
        """
        Create vhd fixed disk format
        """
        Command.run(
            [
                'qemu-img', 'convert', '-f', 'raw', self.diskname,
                '-O', 'vpc'
            ] + self.options + [
                self.get_target_file_path_for_format(self.image_format)
            ]
        )
        if self.tag:
            self._write_vhd_tag(self.tag)

    def store_to_result(self, result):
        """
        Store result file of the vhdfixed format conversion into the
        provided result instance. In this case compressing the result
        is preferred as vhdfixed is not a compressed or dynamic format.

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.get_target_file_path_for_format(
                self.image_format
            ),
            use_for_bundle=True,
            compress=True,
            shasum=True
        )

    def _pack_net_guid_tag(self, tag):
        """
        Pack tag format into 16 byte binary representation. String format
        of the tag is: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

        :param string tag: tagname
        """
        tag_format = re.match(
            ''.join(
                [
                    '^',
                    '([0-9a-f]{8})',
                    '-',
                    '([0-9a-f]{4})',
                    '-',
                    '([0-9a-f]{4})',
                    '-',
                    '([0-9a-f]{4})',
                    '-',
                    '([0-9a-f]{12})',
                    '$'
                ]
            ), tag
        )
        if not tag_format:
            raise KiwiVhdTagError(
                'disk tag %s does not match format' % tag
            )

        # pack first nibble into 4 byte unsigned long type
        binary_tag_part_1 = struct.pack(
            'I', list(struct.unpack('>L', unhexlify(tag_format.group(1))))[0]
        )
        # pack second nibble into 2 byte unsigned short type
        binary_tag_part_2 = struct.pack(
            'H', list(struct.unpack('>H', unhexlify(tag_format.group(2))))[0]
        )
        # pack third nibble into 2 byte unsigned short type
        binary_tag_part_3 = struct.pack(
            'H', list(struct.unpack('>H', unhexlify(tag_format.group(3))))[0]
        )
        # pack fourth nibble into hex
        binary_tag_part_4 = unhexlify(tag_format.group(4))
        # pack fifth nibble into hex
        binary_tag_part_5 = unhexlify(tag_format.group(5))
        return binary_tag_part_1 + binary_tag_part_2 + \
            binary_tag_part_3 + binary_tag_part_4 + \
            binary_tag_part_5

    def _write_vhd_tag(self, tag):
        """
        Azure service uses a tag injected into the disk
        image to identify the OS. The tag is 512B long,
        starting with a GUID, and is placed at a 64K offset
        from the start of the disk image.
        +------------------------------+
        | jump       | GUID(16B)000... |
        +------------------------------|
        | 64K offset | TAG (512B)      |
        +------------+-----------------+
        """
        binary_tag = self._pack_net_guid_tag(tag)
        vhd_fixed_image = self.get_target_file_path_for_format('vhdfixed')
        # seek to 64k offset and zero out 512 byte
        with open(vhd_fixed_image, 'r+b') as vhd_fixed:
            with open('/dev/zero', 'rb') as null:
                vhd_fixed.seek(65536, 0)
                vhd_fixed.write(null.read(512))
                vhd_fixed.seek(0, 2)

        # seek to 64k offset and write tag
        with open(vhd_fixed_image, 'r+b') as vhd_fixed:
            vhd_fixed.seek(65536, 0)
            vhd_fixed.write(binary_tag)
            vhd_fixed.seek(0, 2)
