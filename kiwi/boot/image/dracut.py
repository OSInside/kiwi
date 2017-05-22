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
from kiwi.logger import log
from kiwi.command import Command
from kiwi.system.kernel import Kernel
from kiwi.boot.image.base import BootImageBase


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
        Call dracut as chroot operation to create the initrd and move
        the result into the image build target directory

        :param object mbrid: unused
        """
        if self.is_prepared():
            log.info('Creating generic dracut initrd archive')
            kernel_info = Kernel(self.boot_root_directory)
            kernel_details = kernel_info.get_kernel(raise_on_not_found=True)
            dracut_initrd_basename = self.initrd_base_name + '.xz'
            Command.run(
                [
                    'chroot', self.boot_root_directory,
                    'dracut', '--force',
                    '--no-hostonly',
                    '--no-hostonly-cmdline',
                    '--xz',
                    dracut_initrd_basename,
                    kernel_details.version
                ]
            )
            Command.run(
                [
                    'mv',
                    os.sep.join(
                        [self.boot_root_directory, dracut_initrd_basename]
                    ),
                    self.target_dir
                ]
            )
            self.initrd_filename = os.sep.join(
                [self.target_dir, dracut_initrd_basename]
            )
