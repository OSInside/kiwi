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

# project
from kiwi.utils.compress import Compress

from kiwi.exceptions import (
    KiwiFileNotFound
)


class Checksum:
    """
    **Manage checksum creation for files**

    :param str source_filename: source file name to build checksum for
    :param str checksum_filename: target file with checksum information
    """
    def __init__(self, source_filename):
        if not os.path.exists(source_filename):
            raise KiwiFileNotFound(
                'checksum source file %s not found' % source_filename
            )
        self.source_filename = source_filename
        self.checksum_filename = None
        self.ascii = encoding.getregentry().name

    def matches(self, checksum, filename):
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

    def md5(self, filename=None):
        """
        Create md5 checksum

        :param str filename: filename for checksum

        :return: checksum

        :rtype: str
        """
        md5_checksum = self._calculate_hash_hexdigest(
            hashlib.md5(), self.source_filename
        )
        if filename:
            self._create_checksum_file(
                md5_checksum, filename
            )
        return md5_checksum

    def sha256(self, filename=None):
        """
        Create sha256 checksum

        :param str filename: filename for checksum
        """
        sha256_checksum = self._calculate_hash_hexdigest(
            hashlib.sha256(), self.source_filename
        )
        if filename:
            self._create_checksum_file(
                sha256_checksum, filename
            )
        return sha256_checksum

    def _create_checksum_file(self, checksum, filename):
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
            blocks = self._block_list(
                os.path.getsize(compress.uncompressed_filename)
            )
            checksum = self._calculate_hash_hexdigest(
                hashlib.md5(), compress.uncompressed_filename
            )
        else:
            blocks = self._block_list(
                os.path.getsize(self.source_filename)
            )
        with open(filename, encoding=self.ascii, mode='w') as checksum_file:
            if compressed_blocks:
                checksum_file.write(
                    '%s %s %s %s %s\n' % (
                        checksum, blocks.blocks, blocks.blocksize,
                        compressed_blocks.blocks, compressed_blocks.blocksize
                    )
                )
            else:
                checksum_file.write(
                    '%s %s %s\n' % (
                        checksum, blocks.blocks, blocks.blocksize
                    )
                )

    def _calculate_hash_hexdigest(self, digest, filename, digest_blocks=128):
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

    def _block_list(self, file_size):
        """
        Calculates the number of blocks and the block size for a given file
        size in bytes.

        :param int file_size: files size in bytes.

        :return: int:blocksize, int:blocks

        :rtype: tuple
        """
        blocksize = self._block_size(file_size)
        blocks = int(file_size / blocksize)
        block_list = namedtuple(
            'block_list', ['blocksize', 'blocks']
        )
        return block_list(
            blocksize=blocksize,
            blocks=blocks
        )

    @staticmethod
    def _block_size(number, max_size=8192):
        """
        Compute maximal block size equal to a product of the first
        prime factors of the given number.

        :param int number: number to factorize
        :param int max_size: maximal value for block size

        :return: int: block size
        :rtype: int
        """
        n = number
        bs = 1
        for i in Checksum.primes(max_size):
            while n % i == 0:
                _bs = bs * i
                if _bs > max_size:
                    return bs
                bs = _bs
                n = n // i
                if n == 1:
                    return bs
        return bs

    _primes = [2, 3, 5, 7, 11, 13]

    @classmethod
    def _update_primes(cls, n):
        if n <= cls._primes[-1]:
            return
        _n = int(n**0.5) + 1
        cls._update_primes(_n)

        start = cls._primes[-1] + 1
        for i in range(start, n + 1):
            prime = True
            for p in cls.primes(_n):
                if i % p == 0:
                    prime = False
                    break
            if prime:
                cls._primes.append(i)

    @classmethod
    def primes(cls, number):
        """
        Get prime numbers no greater than given number.

        :param int number: highest possible number to return.

        :rtype: int generator
        """
        if number > cls._primes[-1]:
            cls._update_primes(number)
        for p in cls._primes:
            if p <= number:
                yield p
            else:
                break
