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

# project
from kiwi.firmware import FirmWare
from kiwi.storage.loop_device import LoopDevice
from kiwi.partitioner import Partitioner
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.storage.subformat import DiskFormat
from kiwi.utils.size import StringToSize

from kiwi.exceptions import (
    KiwiImageResizeError
)

log = logging.getLogger('kiwi')


class ImageResizeTask(CliTask):
    """
    Implements resizing of disk images and their disk format

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):
        """
        reformats raw disk image and its format to a new disk
        geometry using the qemu tool chain
        """
        self.manual = Help()
        if self.command_args.get('help') is True:
            return self.manual.show('kiwi::image::resize')

        abs_target_dir_path = os.path.abspath(
            self.command_args['--target-dir']
        )

        if self.command_args['--root']:
            image_root = os.path.abspath(
                os.path.normpath(self.command_args['--root'])
            )
        else:
            image_root = os.sep.join(
                [abs_target_dir_path, 'build', 'image-root']
            )

        self.load_xml_description(
            image_root, self.global_args['--kiwi-file']
        )

        disk_format = self.xml_state.build_type.get_format()

        with DiskFormat.new(
            disk_format or 'raw', self.xml_state, image_root,
            abs_target_dir_path
        ) as image_format:
            if not image_format.has_raw_disk():
                raise KiwiImageResizeError(
                    'no raw disk image {0} found in build results'.format(
                        image_format.diskname
                    )
                )

            new_disk_size = StringToSize.to_bytes(self.command_args['--size'])

            # resize raw disk
            log.info(
                f'Resizing raw disk to {new_disk_size} bytes'
            )
            resize_result = image_format.resize_raw_disk(new_disk_size)

            # resize raw disk partition table
            firmware = FirmWare(self.xml_state)
            with LoopDevice(image_format.diskname) as loop_provider:
                loop_provider.create(overwrite=False)
                partitioner = Partitioner.new(
                    firmware.get_partition_table_type(), loop_provider
                )
                partitioner.resize_table()

            # resize disk format from resized raw disk
            if disk_format and resize_result is True:
                log.info(
                    f'Creating {disk_format} disk format from resized raw disk'
                )
                image_format.create_image_format()
            elif resize_result is False:
                log.info(
                    f'Raw disk is already at {new_disk_size} bytes'
                )
