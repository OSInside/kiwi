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
from tempfile import mkdtemp
from ...command import Command
from ...logger import log

from ...exceptions import(
    KiwiTargetDirectoryNotFound
)


class BootImageBase(object):
    """
        Base class for boot image(initrd) task
    """
    def __init__(self, xml_state, target_dir, root_dir=None):
        self.xml_state = xml_state
        self.target_dir = target_dir
        self.initrd_filename = None
        self.temp_boot_root_directory = None

        self.boot_root_directory = root_dir
        if not self.boot_root_directory:
            self.boot_root_directory = mkdtemp(
                prefix='boot-image.', dir=self.target_dir
            )

        if not os.path.exists(target_dir):
            raise KiwiTargetDirectoryNotFound(
                'target directory %s not found' % target_dir
            )

    def prepare(self):
        """
            prepare new root system to create initrd from. Implementation
            is only needed if there is no other root system available
        """
        raise NotImplementedError

    def create_initrd(self):
        """
            implements creation of the initrd
        """
        raise NotImplementedError

    def is_prepared(self):
        return os.listdir(self.boot_root_directory)

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        temp_directories = [
            self.boot_root_directory,
            self.temp_boot_root_directory
        ]
        for directory in temp_directories:
            if directory and os.path.exists(directory):
                Command.run(
                    ['rm', '-r', '-f', directory]
                )
