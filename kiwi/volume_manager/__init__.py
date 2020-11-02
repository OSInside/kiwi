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
from typing import (
    Dict, List
)
from abc import (
    ABCMeta,
    abstractmethod
)

# project
from kiwi.exceptions import KiwiVolumeManagerSetupError


class VolumeManager(metaclass=ABCMeta):
    """
    **VolumeManager factory**

    :param str name: volume management name
    :param dict device_map:
        dictionary of low level DeviceProvider intances
    :param str root_dir: root directory path name
    :param list volumes: list of volumes from :class:`XMLState::get_volumes()`
    :param dict custom_args: dictionary of custom volume manager arguments
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        name: str, device_map: object, root_dir: str,
        volumes: List, custom_args: Dict = None
    ):
        name_map = {
            'lvm': 'LVM',
            'btrfs': 'Btrfs'
        }
        try:
            volume_manager = importlib.import_module(
                'kiwi.volume_manager.{0}'.format(name)
            )
            module_name = 'VolumeManager{0}'.format(name_map[name])
            return volume_manager.__dict__[module_name](
                device_map, root_dir, volumes, custom_args
            )
        except Exception as issue:
            raise KiwiVolumeManagerSetupError(
                'Support for {0} volume manager not implemented: {1}'.format(
                    name, issue
                )
            )
