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
import platform

# project
from kiwi.filesystem.base import FileSystemBase
from kiwi.command import Command


class FileSystemSquashFs(FileSystemBase):
    """
    **Implements creation of squashfs filesystem**
    """
    def create_on_file(self, filename, label=None, exclude=None):
        """
        Create squashfs filesystem from data tree

        There is no label which could be set for squashfs
        thus this parameter is not used

        :param string filename: result file path name
        :param string label: unused
        :param list exclude: list of exclude dirs/files
        """
        exclude_options = []

        if '-comp' not in self.custom_args['create_options']:
            self.custom_args['create_options'].append('-comp')
            self.custom_args['create_options'].append('xz')

        if '-Xbcj' not in self.custom_args['create_options']:
            host_architecture = platform.machine()
            if '86' in host_architecture:
                self.custom_args['create_options'].append('-Xbcj')
                self.custom_args['create_options'].append('x86')
            if 'ppc' in host_architecture:
                self.custom_args['create_options'].append('-Xbcj')
                self.custom_args['create_options'].append('powerpc')

        if exclude:
            exclude_options.append('-e')
            for item in exclude:
                exclude_options.append(item)

        Command.run(
            [
                'mksquashfs', self.root_dir, filename, '-noappend', '-b', '1M'
            ] + self.custom_args['create_options'] + exclude_options
        )
