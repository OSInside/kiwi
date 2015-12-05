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
import os
from math import sqrt
from collections import namedtuple
import hashlib

# project
from command import Command
from compress import Compress

from exceptions import (
    KiwiFileNotFound
)


class Checksum(object):
    """
        manage checksum creation for files
    """
    def __init__(self, source_filename):
        if not os.path.exists(source_filename):
            raise KiwiFileNotFound(
                'checksum source file %s not found' % source_filename
            )
        self.source_filename = source_filename
        self.checksum_filename = None

    def md5(self, filename):
        compressed_blocks = None
        compress = Compress(self.source_filename)
        if compress.get_format():
            compressed_blocks = self.__block_list(
                os.path.getsize(self.source_filename)
            )
            compress.uncompress(temporary=True)
            blocks = self.__block_list(
                os.path.getsize(compress.uncompressed_filename)
            )
        else:
            blocks = self.__block_list(
                os.path.getsize(self.source_filename)
            )
        with open(self.source_filename) as source:
            checksum = hashlib.md5(source.read()).hexdigest()
        with open(filename, 'w') as md5:
            if compressed_blocks:
                md5.write(
                    '%s %s %s %s %s\n' % (
                        checksum, blocks.blocks, blocks.blocksize,
                        compressed_blocks.blocks, compressed_blocks.blocksize
                    )
                )
            else:
                md5.write(
                    '%s %s %s\n' % (
                        checksum, blocks.blocks, blocks.blocksize
                    )
                )

    def __block_list(self, file_size):
        blocksize = 1
        for factor in self.__prime_factors(file_size):
            if blocksize * factor > 8192:
                break
            blocksize *= factor
        blocks = int(file_size / blocksize)
        block_list = namedtuple(
            'block_list', ['blocksize', 'blocks']
        )
        return block_list(
            blocksize=blocksize,
            blocks=blocks
        )

    def __prime_factors(self, number):
        factor_call = Command.run(['factor', format(number)])
        for factor in factor_call.output.split(':')[1].lstrip().split(' '):
            yield int(factor)
