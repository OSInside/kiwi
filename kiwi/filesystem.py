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
from filesystem_ext2 import FileSystemExt2
from filesystem_ext3 import FileSystemExt3
from filesystem_ext4 import FileSystemExt4
from filesystem_btrfs import FileSystemBtrfs
from filesystem_xfs import FileSystemXfs
from filesystem_fat16 import FileSystemFat16
from filesystem_fat32 import FileSystemFat32
from filesystem_squashfs import FileSystemSquashFs
from filesystem_clicfs import FileSystemClicFs

from exceptions import (
    KiwiFileSystemSetupError
)


class FileSystem(object):
    """
        FileSystem factory
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
        else:
            raise KiwiFileSystemSetupError(
                'Support for %s filesystem not implemented' % name
            )
