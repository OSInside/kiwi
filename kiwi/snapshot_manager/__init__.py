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
from kiwi.exceptions import KiwiSnapshotManagerSetupError


class SnapshotManager(metaclass=ABCMeta):
    """
    **SnapshotManager factory**

    :param str name: snapshot management name
    :param str device: storage device node name
    :param str root_dir: root directory path
    :param str mountpoint: mountpoint of the filesystem to snapshot
    :param str root_volume_name: the name of the root volume in case
        snapshots are hosted in a subvolume.
    :param dict custom_args: dictionary of custom snapshot manager arguments
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        name: str, device: str, root_dir: str, mountpoint: str,
        root_volume_name: str, custom_args: Dict = None
    ):
        name_map = {
            'snapper': 'Snapper',
        }
        try:
            snapshot_manager = importlib.import_module(
                'kiwi.snapshot_manager.{0}'.format(name)
            )
            module_name = 'SnapshotManager{0}'.format(name_map[name])
            return snapshot_manager.__dict__[module_name](
                device, root_dir, mountpoint, root_volume_name, custom_args
            )
        except Exception as issue:
            raise KiwiSnapshotManagerSetupError(
                'Support for {0} snapshot manager not implemented: {1}'.format(
                    name, issue
                )
            )
