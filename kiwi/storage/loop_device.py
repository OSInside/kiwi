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
import logging
import time
import pathlib

# project
from kiwi.command import Command
from kiwi.storage.device_provider import DeviceProvider
from kiwi.utils.command_capabilities import CommandCapabilities

from kiwi.exceptions import (
    KiwiLoopSetupError,
    KiwiCommandNotFound,
    KiwiCommandError
)

log = logging.getLogger('kiwi')


class LoopDevice(DeviceProvider):
    """
    **Create and manage loop device file for block operations**

    :param string filename: loop file name to create
    :param int filesize_mbytes: size of the loop file
    :param int blocksize_bytes: blocksize used in loop driver
    """
    def __init__(
        self, filename: str, filesize_mbytes: int = None,
        blocksize_bytes: int = None
    ):
        self.node_name = ''
        if not os.path.exists(filename) and not filesize_mbytes:
            raise KiwiLoopSetupError(
                'Can not create loop file without a size'
            )
        self.filename = filename
        self.filesize_mbytes = filesize_mbytes
        self.blocksize_bytes = blocksize_bytes

    def __enter__(self):
        return self

    def get_device(self) -> str:
        """
        Device node name

        :return: device node name

        :rtype: str
        """
        return self.node_name

    def is_loop(self) -> bool:
        """
        Always True

        :return: True

        :rtype: bool
        """
        return True

    def create(self, overwrite: bool = True):
        """
        Setup a loop device of the blocksize given in the constructor
        The file to loop is created with the size specified in the
        constructor unless an existing one should not be overwritten

        :param bool overwrite: overwrite existing file to loop
        """
        if overwrite:
            qemu_img_size = format(self.filesize_mbytes) + 'M'
            Command.run(
                ['qemu-img', 'create', self.filename, qemu_img_size]
            )
        loop_options = []
        if self.blocksize_bytes and self.blocksize_bytes != 512:
            if CommandCapabilities.has_option_in_help(
                'losetup', '--sector-size', raise_on_error=False
            ):
                loop_options.append('--sector-size')
            else:
                loop_options.append('--logical-blocksize')
            loop_options.append(format(self.blocksize_bytes))
        loop_call = Command.run(
            ['losetup'] + loop_options + ['-f', '--show', self.filename]
        )
        self.node_name = loop_call.output.rstrip(os.linesep)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.node_name:
            try:
                Command.run(['losetup', '-d', self.node_name])
                # loop detach is an async operation, re-use of the device
                # should not be done before the block device has been released
                loop_released = False
                sys_block_loop = pathlib.Path(
                    '/sys/devices/virtual/block/{0}/loop'.format(
                        os.path.basename(self.node_name)
                    )
                )
                for busy in range(0, 100):
                    if not sys_block_loop.is_block_device():
                        loop_released = True
                        break
                    time.sleep(0.1)
                if not loop_released:
                    raise KiwiCommandError(
                        f'Loop device {self.node_name} still attached'
                    )
            except (KiwiCommandError, KiwiCommandNotFound) as issue:
                log.error(
                    'loop cleanup on {0} failed with: {1}'.format(
                        self.node_name, issue
                    )
                )
