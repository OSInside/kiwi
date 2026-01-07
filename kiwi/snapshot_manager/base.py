# Copyright (c) 2025 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from typing import (
    List, Dict, Optional, Any
)

# project
from kiwi.mount_manager import MountManager


class SnapshotManagerBase:
    """
    **Implements base class for snapshots management inferface**

    :param str device: storage device node name
    :param str root_dir: root directory path
    :param str mountpoint: mountpoint of the filesystem to snapshot
    :param str root_volume_name: the name of the root volume in case
        snapshots are hosted in a subvolume.
    :param dict custom_args: dictionary of custom snapshot manager arguments
    """
    def __init__(
        self, device: str, root_dir: str, mountpoint: str,
        root_volume_name: str, custom_args: Optional[Dict[str, Any]] = None
    ) -> None:
        self.device = device
        self.root_dir = root_dir
        self.mountpoint = mountpoint
        self.root_volume_name = root_volume_name
        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Implementation in specialized SnapshotManager class if required
        """
        pass

    def create_first_snapshot(self) -> List[MountManager]:
        raise NotImplementedError

    def setup_first_snapshot(self):
        raise NotImplementedError

    def get_default_snapshot_name(self) -> str:
        raise NotImplementedError
