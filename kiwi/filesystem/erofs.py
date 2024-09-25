# Copyright (c) 2024 SUSE Software Solutions Germany GmbH.  All rights reserved.
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


class FileSystemEroFs(FileSystemBase):
    """
    **Implements creation of erofs filesystem**
    """
    def create_on_file(
        self, filename, label: str = None, exclude: List[str] = None
    ):
        """
        Create erofs filesystem from data tree

        :param string filename: result file path name
        :param string label: volume label
        :param list exclude: list of exclude dirs/files
        """
        self.filename = filename
        exclude_options = []
        compression = self.custom_args.get('compression')
        if compression:
            self.custom_args['create_options'].append('-z')
            self.custom_args['create_options'].append(compression)

        if exclude:
            for item in exclude:
                # item is a glob, but erofs requires a POSIX extended regex.
                # Translate the glob to a regex for correct behaviour.
                #
                # We can't use fnmatch.translate, as that produces a Python regex.
                as_regex = '^' + item.replace('*', '.*') + '$'
                exclude_options.append(f'--exclude-regex={as_regex}')

        if label:
            self.custom_args['create_options'].append('-L')
            self.custom_args['create_options'].append(label)

        Command.run(
            [
                'mkfs.erofs'
            ] + self.custom_args['create_options'] + exclude_options + [
                self.filename, self.root_dir
            ]
        )
