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
import importlib
from typing import Dict, List
from abc import ABCMeta, abstractmethod

# project
from kiwi.storage.device_provider import DeviceProvider
from kiwi.exceptions import KiwiFileSystemSetupError

filesystem_class_map = {
    'ext2': 'Ext2',
    'ext3': 'Ext3',
    'ext4': 'Ext4',
    'btrfs': 'Btrfs',
    'xfs': 'Xfs',
    'fat16': 'Fat16',
    'fat32': 'Fat32',
    'squashfs': 'SquashFs',
    'swap': 'Swap',
    'erofs': 'EroFs',
}


class FileSystem(metaclass=ABCMeta):
    """
    **FileSystem factory**

    :param string name: filesystem name
    :param object device_provider: Instance of DeviceProvider
    :param string root_dir: root directory path name
    :param dict custom_args: dict of custom filesystem arguments
    """

    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        name: str,
        device_provider: DeviceProvider,
        root_dir: str = None,
        custom_args: Dict = None,  # noqa: E252
    ):
        try:
            filesystem = importlib.import_module(
                'kiwi.filesystem.{0}'.format(name)
            )
            return filesystem.__dict__[
                'FileSystem{0}'.format(filesystem_class_map[name])
            ](device_provider, root_dir, custom_args)
        except Exception as issue:
            raise KiwiFileSystemSetupError(
                'Support for {0} filesystem not implemented: {1}'.format(
                    name, issue
                )
            )

    @staticmethod
    def sparse_install_mount_options(name: str) -> List[str]:
        """
        Provide the mount options that the filesystem implementation of
        the given name declares as needed at install time for a sparse
        data sync to be effective.

        Reading the declaration does not require an instance of the
        filesystem. This allows callers that mount a filesystem they
        did not create, as the volume managers do, to apply the same
        options as the filesystem implementation would.

        :param string name: filesystem name

        :return: list of mount options

        :rtype: list
        """
        try:
            filesystem = importlib.import_module(
                'kiwi.filesystem.{0}'.format(name)
            )
            return filesystem.__dict__[
                'FileSystem{0}'.format(filesystem_class_map[name])
            ].sparse_install_mount_options
        except Exception:
            # A filesystem that cannot be looked up declares nothing.
            # Reporting an unsupported filesystem is the task of new(),
            # which is where one gets created.
            return []
