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
from typing import (
    Dict, List
)
import logging

# project
from kiwi.utils.temporary import Temporary
from kiwi.filesystem.base import FileSystemBase
from kiwi.filesystem.ext4 import FileSystemExt4
from kiwi.command import Command
from kiwi.system.size import SystemSize
from kiwi.storage.loop_device import LoopDevice

log = logging.getLogger('kiwi')


class FileSystemClicFs(FileSystemBase):
    """
    **Implements creation of clicfs filesystem**
    """
    def post_init(self, custom_args: Dict = None):
        """
        Post initialization method

        Initialize temporary container_dir directory to store
        clicfs embeded filesystem

        :param dict custom_args: unused
        """
        pass

    def create_on_file(
        self, filename: str, label: str = None, exclude: List[str] = None
    ):
        """
        Create clicfs filesystem from data tree

        There is no label which could be set for clicfs
        thus this parameter is not used

        There is no option to exclude data from clicfs
        thus this parameter is not used

        :param string filename: result file path name
        :param string label: unused
        :param list exclude: unused
        """
        self.filename = filename
        container_dir = Temporary(prefix='kiwi_clicfs.').new_dir()
        clicfs_container_filesystem = container_dir.name + '/fsdata.ext4'
        with LoopDevice(
            clicfs_container_filesystem,
            self._get_container_filesystem_size_mbytes()
        ) as loop_provider:
            loop_provider.create()
            filesystem = FileSystemExt4(
                loop_provider, self.root_dir
            )
            filesystem.create_on_device()
            filesystem.sync_data()
            Command.run(
                ['resize2fs', '-f', loop_provider.get_device(), '-M']
            )

            # force cleanup and umount of container filesystem
            # before mkclicfs is called
            del filesystem

            Command.run(
                ['mkclicfs', clicfs_container_filesystem, self.filename]
            )

    def _get_container_filesystem_size_mbytes(self):
        size = SystemSize(self.root_dir)
        root_dir_mbytes = size.accumulate_mbyte_file_sizes()
        return size.customize(root_dir_mbytes, 'ext4')
