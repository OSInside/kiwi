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
"""
usage: kiwi-ng image resize -h | --help
       kiwi-ng image resize --target-dir=<directory> --size=<size>
           [--root=<directory>]
       kiwi-ng image resize help

commands:
    resize
        for disk based images, allow to resize the image to a new
        disk geometry. The additional space is free and not in use
        by the image. In order to make use of the additional free
        space a repartition process is required like it is provided
        by kiwi's oem boot code. Therefore the resize operation is
        useful for oem image builds most of the time

options:
    --root=<directory>
        the path to the root directory, if not specified kiwi
        searches the root directory in build/image-root below
        the specified target directory

    --size=<size>
        new size of the image. The value is either a size in bytes
        or can be specified with m=MB or g=GB. Example: 20g

    --target-dir=<directory>
        the target directory to expect image build results
"""
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
            image_root
        )

        disk_format = self.xml_state.build_type.get_format()

        image_format = DiskFormat.new(
            disk_format or 'raw', self.xml_state, image_root,
            abs_target_dir_path
        )
        if not image_format.has_raw_disk():
            raise KiwiImageResizeError(
                'no raw disk image {0} found in build results'.format(
                    image_format.diskname
                )
            )

        new_disk_size = StringToSize.to_bytes(self.command_args['--size'])

        # resize raw disk
        log.info(
            'Resizing raw disk to {0} bytes'.format(new_disk_size)
        )
        resize_result = image_format.resize_raw_disk(new_disk_size)

        # resize raw disk partition table
        firmware = FirmWare(self.xml_state)
        loop_provider = LoopDevice(image_format.diskname)
        loop_provider.create(overwrite=False)
        partitioner = Partitioner.new(
            firmware.get_partition_table_type(), loop_provider
        )
        partitioner.resize_table()
        del loop_provider

        # resize disk format from resized raw disk
        if disk_format and resize_result is True:
            log.info(
                'Creating {0} disk format from resized raw disk'.format(
                    disk_format
                )
            )
            image_format.create_image_format()
        elif resize_result is False:
            log.info(
                'Raw disk is already at {0} bytes'.format(new_disk_size)
            )
