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

# project
from .command import Command
from tempfile import NamedTemporaryFile

from .exceptions import (
    KiwiFileNotFound,
    KiwiCompressionFormatUnknown
)


class Compress(object):
    """
        File compression / decompression
    """
    def __init__(self, source_filename, keep_source_on_compress=False):
        if not os.path.exists(source_filename):
            raise KiwiFileNotFound(
                'compression source file %s not found' % source_filename
            )
        self.keep_source = keep_source_on_compress
        self.source_filename = source_filename
        self.supported_zipper = [
            'xz', 'gzip'
        ]
        self.compressed_filename = None
        self.uncompressed_filename = None

    def xz(self):
        options = [
            '--check=crc32',
            '--lzma2=dict=512KiB'
        ]
        if self.keep_source:
            options.append('--keep')
        Command.run(
            ['xz', '-f'] + options + [self.source_filename]
        )
        self.compressed_filename = self.source_filename + '.xz'

    def gzip(self):
        options = [
            '-9'
        ]
        if self.keep_source:
            options.append('--keep')
        Command.run(
            ['gzip', '-f'] + options + [self.source_filename]
        )
        self.compressed_filename = self.source_filename + '.gz'

    def uncompress(self, temporary=False):
        zipper = self.get_format()
        if not zipper:
            raise KiwiCompressionFormatUnknown(
                'could not detect compression format for %s' %
                self.source_filename
            )
        if not temporary:
            Command.run([zipper, '-d', self.source_filename])
            self.uncompressed_filename = self.source_filename
        else:
            self.temp_file = NamedTemporaryFile()
            bash_command = [
                zipper, '-c', '-d', self.source_filename,
                '>', self.temp_file.name
            ]
            Command.run(['bash', '-c', ' '.join(bash_command)])
            self.uncompressed_filename = self.temp_file.name

    def get_format(self):
        for zipper in self.supported_zipper:
            try:
                Command.run([zipper, '-l', self.source_filename])
                return zipper
            except Exception:
                pass
