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
from command import Command


class Users(object):
    """
        Operations on users and groups in a root directory
    """
    def __init__(self, root_dir):
        self.root_dir = root_dir

    def user_exists(self, user_name):
        return self.__search_for(user_name, '/etc/passwd')

    def group_exists(self, group_name):
        return self.__search_for(group_name, '/etc/group')

    def group_add(self, group_name, options):
        Command.run(
            ['chroot', self.root_dir, 'addgroup'] + options + [group_name]
        )

    def user_add(self, user_name, options):
        Command.run(
            ['chroot', self.root_dir, 'useradd'] + options + [user_name]
        )

    def user_modify(self, user_name, options):
        Command.run(
            ['chroot', self.root_dir, 'usermod'] + options + [user_name]
        )

    def setup_home_for_user(self, user_name, group_name, home_path):
        user_and_group = user_name + ':' + group_name
        Command.run(
            ['chroot', self.root_dir, 'chown', '-R', user_and_group, home_path]
        )

    def __search_for(self, name, in_file):
        search = '^' + name + ':'
        try:
            Command.run(
                ['chroot', self.root_dir, 'grep', '-q', search, in_file]
            )
        except Exception:
            return False
        return True
