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
from kiwi.command import Command


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
