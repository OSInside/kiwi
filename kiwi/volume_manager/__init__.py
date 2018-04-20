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
from kiwi.volume_manager.lvm import VolumeManagerLVM
from kiwi.volume_manager.btrfs import VolumeManagerBtrfs

from kiwi.exceptions import (
    KiwiVolumeManagerSetupError
)


class VolumeManager(object):
    """
    **VolumeManager factory**

    :param str name: volume management name
    :param object device_provider: instance of a class based on DeviceProvider
    :param str root_dir: root directory path name
    :param list volumes: list of volumes from :class:`XMLState::get_volumes()`
    :param dict custom_args: dictionary of custom volume manager arguments
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
