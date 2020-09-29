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
from typing import Dict
from abc import (
    ABCMeta,
    abstractmethod
)

# project
from kiwi.exceptions import KiwiFileSystemSetupError


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
        name: str, device_provider: object,
        root_dir: str=None, custom_args: Dict=None  # noqa: E252
    ):
        name_map = {
            'ext2': 'Ext2',
            'ext3': 'Ext3',
            'ext4': 'Ext4',
            'btrfs': 'Btrfs',
            'xfs': 'Xfs',
            'fat16': 'Fat16',
            'fat32': 'Fat32',
            'squashfs': 'SquashFs',
            'clicfs': 'ClicFs',
            'swap': 'Swap'
        }
        try:
            filesystem = importlib.import_module(
                'kiwi.filesystem.{0}'.format(name)
            )
            return filesystem.__dict__['FileSystem{0}'.format(name_map[name])](
                device_provider, root_dir, custom_args
            )
        except Exception as issue:
            raise KiwiFileSystemSetupError(
                'Support for {0} filesystem not implemented: {1}'.format(
                    name, issue
                )
            )
