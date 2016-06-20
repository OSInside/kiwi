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

from tempfile import mkdtemp

# project
from .base import FileSystemBase
from .ext4 import FileSystemExt4
from ..command import Command
from ..system.size import SystemSize
from ..path import Path
from ..storage.loop_device import LoopDevice
from ..logger import log


class FileSystemClicFs(FileSystemBase):
    """
    Implements creation of clicfs filesystem
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom arguments

        Attributes

        * :attr:`container_dir`
            Temporary directory to store clicfs embeded filesystem

        :param dict custom_args: unused
        """
        self.container_dir = None

    def create_on_file(self, filename, label=None, exclude=None):
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
        self.container_dir = mkdtemp(prefix='kiwi_clicfs.')
        clicfs_container_filesystem = self.container_dir + '/fsdata.ext4'
        loop_provider = LoopDevice(
            clicfs_container_filesystem,
            self._get_container_filesystem_size_mbytes()
        )
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
            ['mkclicfs', clicfs_container_filesystem, filename]
        )

    def _get_container_filesystem_size_mbytes(self):
        size = SystemSize(self.root_dir)
        root_dir_mbytes = size.accumulate_mbyte_file_sizes()
        return size.customize(root_dir_mbytes, 'ext4')

    def __del__(self):
        if self.container_dir:
            log.info('Cleaning up %s instance', type(self).__name__)
            Path.wipe(self.container_dir)
