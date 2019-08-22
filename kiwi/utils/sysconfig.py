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


class SysConfig:
    """
    **Read and Write sysconfig style files**

    :param str source_file: source file path
    """
    def __init__(self, source_file):
        self.source_file = source_file
        self.data_dict = {}
        self.data_list = []
        self._read()

    def __setitem__(self, key, value):
        if key not in self.data_dict:
            self.data_list.append(key)
        self.data_dict[key] = value

    def __getitem__(self, key):
        return self.data_dict[key]

    def __contains__(self, key):
        return key in self.data_dict

    def get(self, key):
        return self.data_dict.get(key)

    def write(self):
        """
        Write back source file with changed content but in same order
        """
        with open(self.source_file, 'w') as source:
            for line in self.data_list:
                if line in self.data_dict:
                    key = line
                    value = self.data_dict[key]
                    source.write('{0}={1}'.format(key, value))
                else:
                    source.write(line)

                source.write(os.linesep)

    def _read(self):
        """
        Read file into a list and a key/value dictionary

        Only lines which are not considered a comment and
        containing the structure key=value are parsed into
        the key/value dictionary. In order to keep the order
        of lines a list is stored too. Those lines matching
        the key/value format are stored with their key in
        the list as a placeholder
        """
        if os.path.exists(self.source_file):
            with open(self.source_file) as source:
                for line in source.readlines():
                    line = line.strip()
                    if '#' not in line and '=' in line:
                        elements = line.split('=')
                        key = elements.pop(0).strip()
                        value = '='.join(elements)
                        self.data_dict[key] = value
                        self.data_list.append(key)
                    else:
                        self.data_list.append(line)
