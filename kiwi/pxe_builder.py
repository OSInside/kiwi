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
from internal_boot_image_task import BootImageTask
from filesystem_builder import FileSystemBuilder
from compress import Compress
from checksum import Checksum
from logger import log

from exceptions import (
    KiwiPxeBootImageError
)


class PxeBuilder(object):
    """
        Filesystem based PXE image builder. This results in creating
        a boot image(initrd) plus its appropriate kernel files and the
        root filesystem image with a checksum. The result can be used
        within the kiwi PXE boot infrastructure
    """
    def __init__(self, xml_state, target_dir, source_dir):
        self.compressed = xml_state.build_type.get_compressed()
        self.filesystem = FileSystemBuilder(
            xml_state, target_dir, source_dir
        )
        self.boot_image_task = BootImageTask(
            xml_state, target_dir
        )

    def create(self):
        if not self.boot_image_task.required():
            raise KiwiPxeBootImageError(
                'pxe images requires a boot setup in the type definition'
            )
        log.info('Creating PXE root filesystem image')
        self.filesystem.create()
        self.image = self.filesystem.filename
        if self.compressed:
            log.info('xz compressing root filesystem image')
            compress = Compress(self.image)
            compress.xz()
            self.image = compress.compressed_filename

        log.info('Creating PXE root filesystem MD5 checksum')
        self.filesystem_checksum = self.filesystem.filename + '.md5'
        checksum = Checksum(self.image)
        checksum.md5(self.filesystem_checksum)

        log.info('Creating PXE boot image')
        self.boot_image_task.prepare()
        self.boot_image_task.extract_kernel_files()
        self.boot_image_task.create_initrd()

        # TODO
        # Creation of client config.<MAC>
