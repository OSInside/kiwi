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
from typing import List

# project
from kiwi.filesystem.base import FileSystemBase
from kiwi.command import Command
from kiwi.defaults import Defaults


class FileSystemSquashFs(FileSystemBase):
    """
    **Implements creation of squashfs filesystem**
    """
    def create_on_file(
        self, filename, label: str = None, exclude: List[str] = None
    ):
        """
        Create squashfs filesystem from data tree

        There is no label which could be set for squashfs
        thus this parameter is not used

        :param string filename: result file path name
        :param string label: unused
        :param list exclude: list of exclude dirs/files
        """
        self.filename = filename
        exclude_options = []
        compression = self.custom_args.get('compression')
        call_args = self.custom_args['create_options'].copy()
        if compression is None or compression == 'xz':
            if '-comp' not in self.custom_args['create_options']:
                call_args.append('-comp')
                call_args.append('xz')

            if '-Xbcj' not in self.custom_args['create_options']:
                host_architecture = Defaults.get_platform_name()
                if Defaults.is_x86_arch(host_architecture):
                    call_args.append('-Xbcj')
                    call_args.append('x86')
                if 'ppc' in host_architecture:
                    call_args.append('-Xbcj')
                    call_args.append('powerpc')
        elif compression != 'uncompressed':
            if '-comp' not in self.custom_args['create_options']:
                call_args.append('-comp')
                call_args.append(compression)
        else:
            for flag in ['-noI', '-noD', '-noF', '-noX']:
                if flag not in self.custom_args['create_options']:
                    call_args.append(flag)

        if exclude:
            exclude_options.extend(['-wildcards', '-e'])
            for item in exclude:
                exclude_options.append(item)

        Command.run(
            [
                'mksquashfs', self.root_dir, self.filename,
                '-noappend', '-b', '1M'
            ] + call_args + exclude_options
        )
