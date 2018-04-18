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
import collections

# project
from .command import Command
from .logger import log


class Path(object):
    """
    **Directory path helpers**
    """
    @classmethod
    def sort_by_hierarchy(self, path_list):
        """
        Sort given list of path names by their hierachy in the tree

        Example:

        .. code:: python

            result = Path.sort_by_hierarchy(['/var/lib', '/var'])

        :param list path_list: list of path names

        :return: hierachy sorted path_list

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
        ignore non empty or protected paths and leave them untouched

        :param string path: path name
        """
        Command.run(
            ['rmdir', '--ignore-fail-on-non-empty', path]
        )
        path_elements = path.split(os.sep)
        protected_elements = [
            'boot', 'dev', 'proc', 'run', 'sys', 'tmp'
        ]
        for path_index in reversed(range(0, len(path_elements))):
            sub_path = os.sep.join(path_elements[0:path_index])
            if sub_path:
                if path_elements[path_index - 1] in protected_elements:
                    log.warning(
                        'remove_hierarchy: path {0} is protected'.format(
                            sub_path
                        )
                    )
                    return
                Command.run(
                    ['rmdir', '--ignore-fail-on-non-empty', sub_path]
                )

    @classmethod
    def which(
        self, filename, alternative_lookup_paths=None,
        custom_env=None, access_mode=None
    ):
        """
        Lookup file name in PATH

        :param string filename: file base name
        :param list alternative_lookup_paths: list of additional lookup paths
        :param list custom_env: a custom os.environ
        :param int access_mode: one of the os access modes or a combination of
         them (os.R_OK, os.W_OK and os.X_OK). If the provided access mode
         does not match the file is considered not existing

        :return: absolute path to file or None

        :rtype: str
        """
        lookup_paths = []
        multipart_message = [
            '"%s": ' % filename, 'exists: unknown', 'mode match: not checked'
        ]
        system_path = os.environ.get('PATH')
        if custom_env:
            system_path = custom_env.get('PATH')
        if system_path:
            lookup_paths = system_path.split(os.pathsep)
        if alternative_lookup_paths:
            lookup_paths += alternative_lookup_paths
        multipart_message[0] += 'in paths "%s"' % ':'.join(lookup_paths)
        for path in lookup_paths:
            location = os.path.join(path, filename)
            file_exists = os.path.exists(location)
            multipart_message[1] = 'exists: "%s"' % file_exists
            if access_mode and file_exists:
                mode_match = os.access(location, access_mode)
                multipart_message[2] = 'mode match: "%s"' % mode_match
                if mode_match:
                    return location
            elif file_exists:
                return location

        log.debug(' '.join(multipart_message))
