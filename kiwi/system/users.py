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
from typing import List, Optional

# project
from kiwi.command import Command
from kiwi.path import Path


class Users:
    """
    **Operations on users and groups in a root directory**

    :param str root_dir: root directory path name
    """
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def user_exists(self, user_name: str) -> bool:
        """
        Check if user exists

        :param str user_name: user name

        :return: True|False

        :rtype: bool
        """
        return self._search_for(user_name, '/etc/passwd')

    def group_exists(self, group_name: str) -> bool:
        """
        Check if group exists

        :param str group_name: group name

        :return: True|False

        :rtype: bool
        """
        return self._search_for(group_name, '/etc/group')

    def group_add(self, group_name: str, options: List[str]) -> None:
        """
        Add group with options

        :param str group_name: group name
        :param list options: groupadd options
        """
        Command.run(
            ['chroot', self.root_dir, 'groupadd'] + options + [group_name]
        )

    def user_add(self, user_name: str, options: List[str]) -> None:
        """
        Add user with options

        :param str user_name: user name
        :param list options: useradd options
        """
        # useradd -m creates the home directory itself, but not missing
        # parents. Issue #2493.
        self._create_home_parent(options)
        Command.run(
            ['chroot', self.root_dir, 'useradd'] + options + [user_name]
        )

    def user_modify(self, user_name: str, options: List[str]) -> None:
        """
        Modify user with options

        :param str user_name: user name
        :param list options: usermod options
        """
        Command.run(
            ['chroot', self.root_dir, 'usermod'] + options + [user_name]
        )

    def setup_home_for_user(
        self, user_name: str, group_name: str, home_path: str
    ) -> None:
        """
        Setup user home directory

        :param str user_name: user name
        :param str group_name: group name
        :param str home_path: path name
        """
        user_and_group = user_name + ':' + group_name
        Command.run(
            ['chroot', self.root_dir, 'chown', '-R', user_and_group, home_path]
        )

    def _search_for(self, name, in_file):
        search = '^' + name + ':'
        try:
            Command.run(
                ['chroot', self.root_dir, 'grep', '-q', search, in_file]
            )
        except Exception:
            return False
        return True

    def _create_home_parent(self, options: List[str]) -> None:
        """
        Create missing parent directories for a useradd home path

        useradd creates the home directory given with -d/--home-dir when
        -m is set, but fails if a parent of that path does not exist.
        """
        home_path = self._home_path_from_options(options)
        if not home_path or not home_path.startswith(os.sep):
            return
        parent = os.path.dirname(home_path.rstrip(os.sep))
        if not parent or parent == os.sep:
            return
        Path.create(
            os.path.join(self.root_dir, parent.lstrip(os.sep))
        )

    @staticmethod
    def _home_path_from_options(options: List[str]) -> Optional[str]:
        home_flags = ('-d', '--home', '--home-dir')
        for index, option in enumerate(options):
            if option in home_flags and index + 1 < len(options):
                return options[index + 1]
            for flag in home_flags:
                prefix = flag + '='
                if option.startswith(prefix):
                    return option[len(prefix):]
        return None
