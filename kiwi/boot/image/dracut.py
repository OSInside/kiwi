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
from kiwi.defaults import Defaults
from kiwi.system.profile import Profile
from kiwi.system.setup import SystemSetup


class BootImageDracut(BootImageBase):
    """
    Implements creation of dracut boot(initrd) images.
    """
    def post_init(self):
        """
        Post initialization method

        Initialize empty list of dracut caller options
        """
        self.dracut_options = []

    def include_file(self, filename):
        self.dracut_options.append('--install')
        self.dracut_options.append(filename)

    def prepare(self):
        """
        Prepare kiwi profile environment to be included in dracut initrd
        """
        profile = Profile(self.xml_state)
        defaults = Defaults()
        defaults.to_profile(profile)
        setup = SystemSetup(
            self.xml_state, self.boot_root_directory
        )
        setup.import_shell_environment(profile)
        self.dracut_options.append('--install')
        self.dracut_options.append('/.profile')

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
                    '--xz'
                ] + self.dracut_options + [
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
