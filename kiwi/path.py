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
import logging
import collections
import pathlib
import shutil
from typing import Dict, List, MutableMapping, Optional

# project
from kiwi.command import Command
from kiwi.exceptions import KiwiFileAccessError

log = logging.getLogger('kiwi')


class Path:
    """
    **Directory path helpers**
    """
    @staticmethod
    def sort_by_hierarchy(path_list: List[str]) -> List[str]:
        """
        Sort given list of path names by their hierachy in the tree

        Example:

        .. code:: python

            result = Path.sort_by_hierarchy(['/var/lib', '/var'])

        :param list path_list: list of path names

        :return: hierachy sorted path_list

        :rtype: list
        """
        paths_at_depth: Dict[int, List[str]] = {}
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

    @staticmethod
    def access(path: str, mode: int, **kwargs) -> bool:
        """
        Check whether path can be accessed with the given mode.

        :param str path: The path that should be checked for
            access.

        :param int mode: Which access mode should be checked.
            This value must be a bit-wise or of one or more of the following
            constants: :py:const:`os.F_OK` (note that this one is zero),
            :py:const:`os.X_OK`, :py:const:`os.R_OK` and :py:const:`os.W_OK`

        :param kwargs: further keyword arguments are forwarded to
            :func:`os.access`

        :return: Boolean value whether this access mode is allowed
        :rtype: bool

        :raises ValueError: if the supplied mode is invalid
        :raises kiwi.exceptions.KiwiFileNotFound: if the path does not exist or
            is not accessible by the current user
        """
        if mode & ~(os.F_OK | os.X_OK | os.R_OK | os.W_OK) != 0:
            raise ValueError('Invalid mode 0x{:X}'.format(mode))
        try:
            os.stat(path)
        except Exception as exc:
            raise KiwiFileAccessError(
                'Error accessing path {0} failed with: {1}'.format(path, exc)
            )

        return os.access(path, mode, **kwargs)

    @staticmethod
    def create(path: str) -> None:
        """
        Create path and all sub directories to target

        :param string path: path name
        """
        log.debug("Creating directory %s", path)
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def wipe(path: str) -> None:
        """
        Delete path and all contents

        :param string path: path name
        """
        if os.path.exists(path):
            Command.run(
                ['rm', '-r', '-f', path]
            )

    @staticmethod
    def remove_hierarchy(root: str, path: str) -> None:
        """
        Recursively remove an empty path and its sub directories
        starting at a given root directory. Ignore non empty or
        protected paths and leave them untouched

        :param string root: start at directory
        :param string path: path name below root
        """
        Command.run(
            [
                'rmdir', '--ignore-fail-on-non-empty',
                os.path.normpath(os.sep.join([root, path]))
            ]
        )
        path_elements = path.split(os.sep)
        protected_elements = [
            'boot', 'dev', 'proc', 'run', 'sys', 'tmp', 'home', 'mnt'
        ]
        for path_index in reversed(range(0, len(path_elements))):
            sub_path = os.sep.join(path_elements[0:path_index])
            if sub_path:
                if path_elements[path_index - 1] in protected_elements:
                    log.warning(
                        'remove_hierarchy: path {0} is protected'.format(
                            os.path.normpath(os.sep.join([root, sub_path]))
                        )
                    )
                    return
                Command.run(
                    [
                        'rmdir', '--ignore-fail-on-non-empty',
                        os.path.normpath(os.sep.join([root, sub_path]))
                    ]
                )

    @staticmethod
    def move_to_root(root: str, elements: List[str]) -> List[str]:
        """
        Change the given path elements to a new root directory

        :param str root: the root path to trim
        :param list elements: list of path names

        :return: changed elements

        :rtype: list
        """
        result = []
        for element in elements:
            normalized_element = os.path.normpath(element)
            result.append(
                normalized_element.replace(
                    os.path.normpath(root), os.sep
                ).replace('{0}{0}'.format(os.sep), os.sep)
            )
        return result

    @staticmethod
    def rebase_to_root(root: str, elements: List[str]) -> List[str]:
        """
        Include the root prefix for the given paths elements

        :param str root: the new root path
        :param list elements: list of path names

        :return: changed elements

        :rtype: list
        """
        result = []
        for element in elements:
            result.append(os.path.normpath(os.sep.join([root, element])))
        return result

    @staticmethod
    def which(
        filename: str,
        custom_env: Optional[MutableMapping[str, str]] = None,
        access_mode: int = os.F_OK | os.X_OK,
        root_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Lookup file name in PATH

        :param string filename: file base name
        :param list alternative_lookup_paths: list of additional lookup paths
        :param list custom_env: a custom os.environ used to obtain ``$PATH``
        :param int access_mode: one of the os access modes or a combination of
         them (os.R_OK, os.W_OK and os.X_OK). If the provided access mode
         does not match the file is considered not existing
        :param str root_dir: the root path to look at

        :return: absolute path to file or None

        :rtype: str
        """
        system_path = (custom_env.get("PATH") if custom_env else os.environ.get("PATH")) or os.defpath

        lookup_paths = system_path.split(os.pathsep)
        if root_dir:
            lookup_paths = Path.rebase_to_root(root_dir, lookup_paths)
        log.debug(f"Looking for {filename} in {os.pathsep.join(lookup_paths)}")
        return shutil.which(filename, access_mode, path=os.pathsep.join(lookup_paths))
