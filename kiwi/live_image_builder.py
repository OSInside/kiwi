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
from tempfile import mkdtemp
import platform

# project
from filesystem_squashfs import FileSystemSquashFs
from internal_boot_image_task import BootImageTask
from firmware import FirmWare
from defaults import Defaults
from path import Path
from result import Result

from exceptions import (
    KiwiLiveBootImageError
)


class LiveImageBuilder(object):
    """
        Live image builder
    """
    def __init__(self, xml_state, target_dir, source_dir):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.xml_state = xml_state
        self.flags = xml_state.build_type.get_flags()
        self.volume_id = xml_state.build_type.get_volid()
        self.mbrid = ImageIdentifier()
        self.mbrid.calculate_id()

        self.boot_image_task = BootImageTask(
            xml_state, target_dir
        )
        self.firmware = FirmWare(
            xml_state.build_type.get_firmware()
        )
        self.diskname = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(), '.iso'
            ]
        )
        self.result = Result()

    def create(self):
        if not self.boot_image_task.required():
            raise KiwiLiveBootImageError(
                'live images requires a boot setup in the type definition'
            )

        # media dir to store CD contents
        self.media_dir = mkdtemp(
            prefix='live-media.', dir=self.target_dir
        )

        # custom iso metadata
        self.custom_iso_args = [
            '-A', self.mbrid.get_id(),
            '-allow-limited-size', '-udf',
            '-preparer_id', '"' + Defaults.get_preparer() + '"',
            '-publisher', '"' + Defaults.get_publisher() + '"',
        ]
        if self.volume_id:
            self.custom_iso_args.append('-V')
            self.custom_iso_args.append('"' + self.volume_id + '"')

        # prepare boot(initrd) root system
        log.info('Preparing boot system')
        self.boot_image_task.prepare()

        # pack system into live boot structure
        if not self.flags or self.flags == 'overlay':
            squashed_image_file = ''.join(
                [
                    self.target_dir, '/',
                    self.xml_state.xml_data.get_name(),
                    '-read-only.', platform.machine(), '-',
                    self.xml_sate.get_image_version()
                ]
            )
            squashed_image = FileSystemSquashFs(
                device_provider=None, source_dir=self.source_dir
            )
            squashed_image.create_on_file(squashed_image_file)
            Command.run(
                ['mv', squashed_image_file, self.media_dir]
            )
        else:
            raise KiwiLiveBootImageError(
                'live image structure type "%s" not supported' % self.flags
            )

        # TODO: create config.isoclient

        # TODO: create liveboot

        # TODO: setup bootloader

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        if self.media_dir:
            Path.wipe(self.media_dir)
