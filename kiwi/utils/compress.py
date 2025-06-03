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
import logging
from typing import List, Optional

# project
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiFileNotFound,
    KiwiCompressionFormatUnknown
)

log = logging.getLogger('kiwi')


class Compress:
    """
    **File compression / decompression**

    :param bool keep_source: Request to keep the uncompressed source
    :param str source_filename: Source file name to compress
    :param list supported_zipper: List of supported compression tools
    :param str compressed_filename: Compressed file name path with
        compression suffix
    :param str uncompressed_filename:
        Uncompressed file name path
    """
    def __init__(
        self, source_filename: str, keep_source_on_compress: bool = False
    ) -> None:
        if not os.path.exists(source_filename):
            raise KiwiFileNotFound(
                f'compression source file {source_filename} not found'
            )
        self.keep_source = keep_source_on_compress
        self.source_filename = source_filename
        self.supported_zipper = [
            'xz', 'gzip'
        ]
        self.compressed_filename: Optional[str] = None
        self.uncompressed_filename: Optional[str] = None

    def xz(self, options: Optional[List[str]] = None) -> str:
        """
        Create XZ compressed file

        :param list options: custom xz compression options
        """
        if not options:
            options = Defaults.get_xz_compression_options()
        assert options
        if self.keep_source:
            options.append('--keep')
        Command.run(
            ['xz', '-f'] + options + [self.source_filename]
        )
        self.compressed_filename = self.source_filename + '.xz'
        return self.compressed_filename

    def gzip(self) -> str:
        """
        Create gzip(max compression) compressed file
        """
        options = [
            '-9'
        ]
        if self.keep_source:
            options.append('--keep')
        Command.run(
            ['gzip', '-f'] + options + [self.source_filename]
        )
        self.compressed_filename = self.source_filename + '.gz'
        return self.compressed_filename

    def uncompress(self, temporary: bool = False) -> str:
        """
        Uncompress with format autodetection

        By default the original source file will be changed into
        the uncompressed variant. If temporary is set to True
        a temporary file is created instead

        :param bool temporary: uncompress to a temporary file
        """
        zipper = self.get_format()
        if not zipper:
            raise KiwiCompressionFormatUnknown(
                f'could not detect compression format for {self.source_filename}'
            )
        if not temporary:
            Command.run([zipper, '-d', self.source_filename])
            self.uncompressed_filename = self.source_filename
        else:
            self.temp_file = Temporary().new_file()
            bash_command = [
                zipper, '-c', '-d', self.source_filename,
                '>', self.temp_file.name
            ]
            Command.run(['bash', '-c', ' '.join(bash_command)])
            self.uncompressed_filename = self.temp_file.name
        return self.uncompressed_filename

    def get_format(self) -> Optional[str]:
        """
        Detect compression format

        :return: compression format name or None if it couldn't be inferred

        :rtype: Optional[str]
        """
        for zipper in self.supported_zipper:
            result = Command.run(
                [zipper, '-l', self.source_filename], raise_on_error=False
            )
            if result.returncode == 0:
                return zipper
        return None
