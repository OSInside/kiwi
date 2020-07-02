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
from kiwi.filesystem.ext2 import FileSystemExt2
from kiwi.filesystem.ext3 import FileSystemExt3
from kiwi.filesystem.ext4 import FileSystemExt4
from kiwi.filesystem.btrfs import FileSystemBtrfs
from kiwi.filesystem.xfs import FileSystemXfs
from kiwi.filesystem.fat16 import FileSystemFat16
from kiwi.filesystem.fat32 import FileSystemFat32
from kiwi.filesystem.squashfs import FileSystemSquashFs
from kiwi.filesystem.clicfs import FileSystemClicFs
from kiwi.filesystem.swap import FileSystemSwap

from kiwi.exceptions import (
    KiwiFileSystemSetupError
)


class FileSystem:
    """
    **FileSystem factory**

    :param string name: filesystem name
    :param object device_provider: Instance of DeviceProvider
    :param string root_dir: root directory path name
    :param dict custom_args: dict of custom filesystem arguments
    """
    def __new__(self, name, device_provider, root_dir=None, custom_args=None):
        if name == 'ext2':
            return FileSystemExt2(
                device_provider, root_dir, custom_args
            )
        elif name == 'ext3':
            return FileSystemExt3(
                device_provider, root_dir, custom_args
            )
        elif name == 'ext4':
            return FileSystemExt4(
                device_provider, root_dir, custom_args
            )
        elif name == 'btrfs':
            return FileSystemBtrfs(
                device_provider, root_dir, custom_args
            )
        elif name == 'xfs':
            return FileSystemXfs(
                device_provider, root_dir, custom_args
            )
        elif name == 'fat16':
            return FileSystemFat16(
                device_provider, root_dir, custom_args
            )
        elif name == 'fat32':
            return FileSystemFat32(
                device_provider, root_dir, custom_args
            )
        elif name == 'squashfs':
            return FileSystemSquashFs(
                device_provider, root_dir, custom_args
            )
        elif name == 'clicfs':
            return FileSystemClicFs(
                device_provider, root_dir, custom_args
            )
        elif name == 'swap':
            return FileSystemSwap(
                device_provider, root_dir, custom_args
            )
        else:
            raise KiwiFileSystemSetupError(
                'Support for %s filesystem not implemented' % name
            )
