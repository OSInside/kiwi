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
import csv
from io import TextIOWrapper
from typing import Iterable

# project
from kiwi.exceptions import KiwiOSReleaseImportError


class OsRelease:
    """
    **Read os-release information**
    """
    def __init__(self, root_dir: str):
        self.data = {}
        os_release = root_dir + '/etc/os-release'
        try:
            with open(os_release) as osdata:
                reader = csv.reader(OsRelease._rip(osdata), delimiter='=')
                self.data = dict(reader)
        except Exception as issue:
            raise KiwiOSReleaseImportError(
                f'Import of {os_release} failed with {issue}'
            )

    @staticmethod
    def _is_comment(line: str) -> bool:
        return line.startswith('#')

    @staticmethod
    def _is_whitespace(line: str) -> bool:
        return line.isspace()

    @staticmethod
    def _rip(csvfile: TextIOWrapper) -> Iterable[str]:
        for row in csvfile:
            if not OsRelease._is_comment(row) \
               and not OsRelease._is_whitespace(row):
                yield row

    def get(self, key: str) -> str:
        """
        Return value for key or an empty string if not present

        :param string key: key name from os-release
        """
        return self.data.get(key) or ''
