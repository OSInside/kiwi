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
# project
from volume_manager_lvm import VolumeManagerLVM
from volume_manager_btrfs import VolumeManagerBtrfs

from exceptions import (
    KiwiVolumeManagerSetupError
)


class VolumeManager(object):
    """
        VolumeManager factory
    """
    def __new__(
        self, name, device_provider, root_dir, volumes, custom_args=None
    ):
        if name == 'lvm':
            return VolumeManagerLVM(
                device_provider, root_dir, volumes, custom_args
            )
        elif name == 'btrfs':
            return VolumeManagerBtrfs(
                device_provider, root_dir, volumes, custom_args
            )
        else:
            raise KiwiVolumeManagerSetupError(
                'Support for %s volume manager not implemented' % name
            )
