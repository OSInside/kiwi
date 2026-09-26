# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from tempfile import NamedTemporaryFile
from typing import Dict

# project
from kiwi.path import Path
from kiwi.command import Command


class DirFiles:
    """
    **Directory File Manager**

    Connects registered files to a named temporary file
    and updates the contents of the given directory with
    the registered files in an atomic operation
    """
    def __init__(self, dirname: str) -> None:
        self.dirname = dirname
        self.dirname_tmp = ''.join(
            [self.dirname, '.tmp']
        )
        self.dirname_wipe = ''.join(
            [self.dirname, '.wipe']
        )
        self.collection: Dict[str, str] = {}
        Path.wipe(self.dirname_tmp)

    def register(self, filename: str) -> str:
        """
        Register given filename to be handled as a temporary
        file. The given filename gets overwritten with the
        contents of the temporary file on call of the commit
        method

        :param string filename: file path name

        :return: name of created temporary file

        :rtype: string
        """
        tmpfile = NamedTemporaryFile()
        self.collection[os.path.basename(filename)] = tmpfile.name
        return tmpfile.name

    def deregister(self, filename: str) -> bool:
        """
        Deregister filename from collection if present
        """
        base_file_name = os.path.basename(filename)
        if self.collection.get(base_file_name):
            del self.collection[base_file_name]
            return True
        return False

    def commit(self) -> None:
        """
        Update instance directory with contents of registered files

        Use an atomic operation that prepares a tmp directory with
        all registered files and move it to the directory given at
        instance creation time. Please note the operation is not
        fully atomic as it uses two move commands in a series
        """
        Path.create(self.dirname_tmp)
        bash_command = [
            'cp', '-a', f'{self.dirname}/*', self.dirname_tmp
        ]
        Command.run(
            ['bash', '-c', ' '.join(bash_command)], raise_on_error=False
        )
        for origin, tmpname in list(self.collection.items()):
            Command.run(
                ['mv', tmpname, os.sep.join([self.dirname_tmp, origin])]
            )
        Command.run(
            ['mv', self.dirname, self.dirname_wipe]
        )
        Command.run(
            ['mv', self.dirname_tmp, self.dirname]
        )
        Command.run(
            ['rm', '-rf', self.dirname_wipe]
        )
