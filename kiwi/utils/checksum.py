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
from collections import namedtuple
import hashlib
import encodings.ascii as encoding
from typing import Any, Callable, Optional

# project
from kiwi.api_helper import decommissioned
from kiwi.utils.compress import Compress
from kiwi.utils.primes import factors

from kiwi.exceptions import KiwiFileNotFound


class Checksum:
    """
    **Manage checksum creation for files**

    :param str source_filename: source file name to build checksum for
    :param str checksum_filename: target file with checksum information
    """

    def __init__(self, source_filename: str) -> None:
        if not os.path.exists(source_filename):
            raise KiwiFileNotFound(
                f'checksum source file {source_filename} not found'
            )
        self.source_filename = source_filename
        self.checksum_filename = None
        self.ascii = encoding.getregentry().name

    def matches(self, checksum: str, filename: str) -> bool:
        """
        Compare given checksum with reference checksum stored
        in the provided filename. If the checksum matches the
        method returns True, or False in case it does not match

        :param str checksum: checksum string to compare
        :param str filename: filename containing checksum

        :return: True or False

        :rtype: bool
        """
        if not os.path.exists(filename):
            return False
        with open(filename, encoding=self.ascii) as checksum_file:
            checksum_from_file = checksum_file.read()
            # checksum is expected to be stored in the first field
            # separated by space, other information might contain
            # the filename or blocklist data which is not of interest
            # for the plain checksum match
            if checksum_from_file.split(' ')[0] == checksum:
                return True
        return False

    @decommissioned
    def md5(self, filename: Optional[str] = None) -> None:
        pass  # pragma: no cover

    def sha256(self, filename: Optional[str] = None) -> str:
        """
        Create sha256 checksum

        :param str filename: filename for checksum
        """
        sha256_checksum = self._calculate_hash_hexdigest(
            hashlib.sha256(), self.source_filename
        )
        if filename:
            self._create_checksum_file(
                sha256_checksum, filename, hashlib.sha256
            )
        return sha256_checksum

    def sha512(self, filename: Optional[str] = None) -> str:
        """
        Create sha512 checksum

        :param str filename: filename for checksum
        """
        sha512_checksum = self._calculate_hash_hexdigest(
            hashlib.sha512(), self.source_filename
        )
        if filename:
            self._create_checksum_file(
                sha512_checksum, filename, hashlib.sha512
            )
        return sha512_checksum

    def _create_checksum_file(
        self,
        checksum: str,
        filename: str,
        haslib_method: Callable[[], 'hashlib._Hash'],
    ) -> None:
        """
        Creates the text file that contains the checksum

        :param str checksum: checksum to include into the file
        :param str filename: filename of the output file
        """
        compressed_blocks = None
        compress = Compress(self.source_filename)
        if compress.get_format():
            compressed_blocks = self._block_list(
                os.path.getsize(self.source_filename)
            )
            compress.uncompress(temporary=True)
            assert compress.uncompressed_filename is not None
            blocks = self._block_list(
                os.path.getsize(compress.uncompressed_filename)
            )
            checksum = self._calculate_hash_hexdigest(
                haslib_method(), compress.uncompressed_filename
            )
        else:
            blocks = self._block_list(os.path.getsize(self.source_filename))
        with open(filename, encoding=self.ascii, mode='w') as checksum_file:
            if compressed_blocks:
                checksum_file.write(
                    '%s %s %s %s %s\n'
                    % (
                        checksum,
                        blocks.blocks,
                        blocks.blocksize,
                        compressed_blocks.blocks,
                        compressed_blocks.blocksize,
                    )
                )
            else:
                checksum_file.write(
                    f'{checksum} {blocks.blocks} {blocks.blocksize}\n'
                )

    def _calculate_hash_hexdigest(
        self, digest: 'hashlib._Hash', filename: str, digest_blocks: int = 128
    ) -> str:
        """
        Calculates the hash hexadecimal digest for a given file.

        :param func digest: Digest function for hash calculation
        :param str filename: File to compute
        :param int digest_blocks: Number of blocks processed at a time
        """
        chunk_size = digest_blocks * digest.block_size
        with open(filename, 'rb') as source:
            for chunk in iter(lambda: source.read(chunk_size), b''):
                digest.update(chunk)
        return digest.hexdigest()

    def _block_list(self, file_size: int) -> Any:
        """
        Calculates the number of blocks and the block size for a given file
        size in bytes.

        :param int file_size: files size in bytes.

        :return: int:blocksize, int:blocks

        :rtype: tuple
        """
        blocksize = 1
        for factor in factors(file_size, 8192):
            if blocksize * factor > 8192:
                break
            blocksize *= factor
        blocks = int(file_size / blocksize)
        block_list = namedtuple('block_list', ['blocksize', 'blocks'])
        return block_list(blocksize=blocksize, blocks=blocks)
