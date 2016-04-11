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
import collections

# project
from .command import Command


class Path(object):
    """
    Directory path helpers
    """
    @classmethod
    def sort_by_hierarchy(self, path_list):
        """
        Sort given list of path names by their hierachy in the tree

        :param list path_list: list of path names

        :return: sorted path_list
        :rtype: list
        """
        paths_at_depth = {}
        for path in path_list:
            path_elements = path.split('/')
            path_depth = len(path_elements)
            if path_depth not in paths_at_depth:
                paths_at_depth[path_depth] = []
            paths_at_depth[path_depth].append(path)
        ordered_paths_at_depth = collections.OrderedDict(
            sorted(paths_at_depth.items())
        )
        ordered_paths = []
        for path_depth in ordered_paths_at_depth:
            for path in ordered_paths_at_depth[path_depth]:
                ordered_paths.append(path)
        return ordered_paths

    @classmethod
    def create(self, path):
        """
        Create path and all sub directories to target

        :param string path: path name
        """
        Command.run(
            ['mkdir', '-p', path]
        )

    @classmethod
    def wipe(self, path):
        """
        Delete path and all contents

        :param string path: path name
        """
        Command.run(
            ['rm', '-r', '-f', path]
        )

    @classmethod
    def remove(self, path):
        """
        Delete empty path, causes an error if target is not empty

        :param string path: path name
        """
        Command.run(
            ['rmdir', path]
        )

    @classmethod
    def remove_hierarchy(self, path):
        """
        Recursively remove an empty path and its sub directories
        ignore non empty paths and leave them untouched

        :param string path: path name
        """
        Command.run(
            ['rmdir', '-p', '--ignore-fail-on-non-empty', path]
        )
