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
from command import Command
from filesystem_base import FileSystemBase
from filesystem_ext4 import FileSystemExt4
from system_size import SystemSize
from tempfile import mkdtemp
from path import Path
from loop_device import LoopDevice
from logger import log


class FileSystemClicFs(FileSystemBase):
    """
        Implements creation of clicfs filesystem
    """
    def post_init(self, custom_args):
        self.container_dir = None
        self.custom_args = custom_args

    def create_on_file(self, filename, label=None):
        # there is no label which could be set for clicfs
        # thus this parameter is not used
        self.container_dir = mkdtemp()
        clicfs_container_filesystem = self.container_dir + '/fsdata.ext4'
        loop_provider = LoopDevice(
            clicfs_container_filesystem,
            self.__get_container_filesystem_size_mbytes()
        )
        filesystem = FileSystemExt4(
            loop_provider, self.source_dir
        )
        filesystem.create_on_device()
        Command.run(
            ['resize2fs', loop_provider.get_device(), '-M']
        )
        filesystem.sync_data()

        # force cleanup and umount of container filesystem
        # before mkclicfs is called
        del filesystem

        Command.run(
            ['mkclicfs', clicfs_container_filesystem, filename]
        )

    def __get_container_filesystem_size_mbytes(self):
        size = SystemSize(self.source_dir)
        source_dir_mbytes = size.accumulate_mbyte_file_sizes()
        return size.customize(source_dir_mbytes, 'ext4')

    def __del__(self):
        if self.container_dir:
            log.info('Cleaning up %s instance', type(self).__name__)
            Path.wipe(self.container_dir)
