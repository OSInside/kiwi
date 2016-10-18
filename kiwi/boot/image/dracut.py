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
import os

# project
from ...utils.compress import Compress
from ...logger import log
from ...command import Command
from ...system.kernel import Kernel
from .base import BootImageBase


class BootImageDracut(BootImageBase):
    """
    Implements creation of dracut boot(initrd) images.
    """
    def prepare(self):
        """
        For dracut no further preparation steps are required.
        dracut is called as chroot operation in the system tree.
        No extra caller environment will be created in this case
        """
        pass

    def create_initrd(self, mbrid=None):
        """
        Call dracut to create the initrd and XZ compress the result

        :param object mbrid: unused
        """
        if self.is_prepared():
            log.info('Creating generic dracut initrd archive')
            kernel_info = Kernel(self.boot_root_directory)
            kernel_version = kernel_info.get_kernel().version
            Command.run(
                [
                    'chroot', self.boot_root_directory,
                    'dracut', '--force',
                    '--no-hostonly',
                    '--no-hostonly-cmdline',
                    '--no-compress',
                    os.path.basename(self.initrd_file_name),
                    kernel_version
                ]
            )
            Command.run(
                [
                    'mv',
                    self.boot_root_directory + '/' + os.path.basename(
                        self.initrd_file_name
                    ),
                    self.initrd_file_name
                ]
            )
            log.info(
                '--> xz compressing archive'
            )
            compress = Compress(self.initrd_file_name)
            compress.xz()
            self.initrd_filename = compress.compressed_filename
