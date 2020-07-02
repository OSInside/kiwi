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
from kiwi.filesystem.base import FileSystemBase
from kiwi.command import Command
from kiwi.defaults import Defaults


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
        compression = self.custom_args.get('compression')
        if compression is None or compression == 'xz':
            if '-comp' not in self.custom_args['create_options']:
                self.custom_args['create_options'].append('-comp')
                self.custom_args['create_options'].append('xz')

            if '-Xbcj' not in self.custom_args['create_options']:
                host_architecture = Defaults.get_platform_name()
                if Defaults.is_x86_arch(host_architecture):
                    self.custom_args['create_options'].append('-Xbcj')
                    self.custom_args['create_options'].append('x86')
                if 'ppc' in host_architecture:
                    self.custom_args['create_options'].append('-Xbcj')
                    self.custom_args['create_options'].append('powerpc')
        elif compression != 'uncompressed':
            if '-comp' not in self.custom_args['create_options']:
                self.custom_args['create_options'].append('-comp')
                self.custom_args['create_options'].append(compression)
        else:
            for flag in ['-noI', '-noD', '-noF', '-noX']:
                if flag not in self.custom_args['create_options']:
                    self.custom_args['create_options'].append(flag)

        if exclude:
            exclude_options.extend(['-wildcards', '-e'])
            for item in exclude:
                exclude_options.append(item)

        Command.run(
            [
                'mksquashfs', self.root_dir, filename, '-noappend', '-b', '1M'
            ] + self.custom_args['create_options'] + exclude_options
        )
