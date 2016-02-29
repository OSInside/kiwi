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
from ..command import Command
from .device_provider import DeviceProvider
from ..logger import log

from ..exceptions import (
    KiwiLoopSetupError
)


class LoopDevice(DeviceProvider):
    """
        Create and manage loop device file for block operations
    """
    def __init__(self, filename, filesize_mbytes=None, blocksize_bytes=None):
        self.node_name = None
        if not os.path.exists(filename) and not filesize_mbytes:
            raise KiwiLoopSetupError(
                'Can not create loop file without a size'
            )
        self.filename = filename
        self.filesize_mbytes = filesize_mbytes
        self.blocksize_bytes = blocksize_bytes

    def get_device(self):
        return self.node_name

    def is_loop(self):
        return True

    def create(self):
        qemu_img_size = format(self.filesize_mbytes) + 'M'
        Command.run(
            ['qemu-img', 'create', self.filename, qemu_img_size]
        )
        loop_options = []
        if self.blocksize_bytes and self.blocksize_bytes != 512:
            loop_options.append('-L')
            loop_options.append(format(self.blocksize_bytes))
        loop_call = Command.run(
            ['losetup'] + loop_options + ['-f', '--show', self.filename]
        )
        self.node_name = loop_call.output.rstrip('\n')

    def __del__(self):
        if self.node_name:
            log.info('Cleaning up %s instance', type(self).__name__)
            try:
                Command.run(['losetup', '-d', self.node_name])
            except Exception:
                log.warning(
                    'loop device %s still busy', self.node_name
                )
