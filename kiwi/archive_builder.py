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
import platform

# project
from defaults import Defaults
from archive_tar import ArchiveTar
from checksum import Checksum
from logger import log
from result import Result

from exceptions import (
    KiwiArchiveSetupError
)


class ArchiveBuilder(object):
    """
        root archive image builder
    """
    def __init__(self, xml_state, target_dir, root_dir):
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.xml_state = xml_state
        self.requested_archive_type = xml_state.get_build_type_name()
        self.result = Result(xml_state)
        self.filename = self.__target_file_for('tar.xz')
        self.checksum = self.__target_file_for('md5')

    def create(self):
        supported_archives = Defaults.get_archive_image_types()
        if self.requested_archive_type not in supported_archives:
            raise KiwiArchiveSetupError(
                'Unknown archive type: %s' % self.requested_archive_type
            )

        if self.requested_archive_type == 'tbz':
            log.info('Creating XZ compressed tar archive')
            archive = ArchiveTar(
                self.__target_file_for('tar')
            )
            archive.create_xz_compressed(self.root_dir)
            checksum = Checksum(self.filename)
            log.info('--> Creating archive checksum')
            checksum.md5(self.checksum)
            self.result.add(
                'root_archive', self.filename
            )
            self.result.add(
                'root_archive_md5', self.checksum
            )
        return self.result

    def __target_file_for(self, suffix):
        return ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + self.xml_state.get_image_version(),
                '.', suffix
            ]
        )
