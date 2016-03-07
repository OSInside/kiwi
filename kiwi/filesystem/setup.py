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
from ..system.size import SystemSize
from ..logger import log
from ..defaults import Defaults


class FileSystemSetup(object):
    """
        Implement filesystem setup methods providing information
        from the root directory required before building a
        filesystem image
    """
    def __init__(self, xml_state, root_dir):
        self.configured_size = xml_state.get_build_type_size()
        self.size = SystemSize(root_dir)
        self.requested_image_type = xml_state.get_build_type_name()
        if self.requested_image_type in Defaults.get_filesystem_image_types():
            self.requested_filesystem = self.requested_image_type
        else:
            self.requested_filesystem = xml_state.build_type.get_filesystem()

    def get_size_mbytes(self):
        root_dir_mbytes = self.size.accumulate_mbyte_file_sizes()
        filesystem_mbytes = self.size.customize(
            root_dir_mbytes, self.requested_filesystem
        )

        if not self.configured_size:
            log.info(
                'Using calculated size: %d MB',
                filesystem_mbytes
            )
            return filesystem_mbytes
        elif self.configured_size.additive:
            result_filesystem_mbytes = \
                self.configured_size.mbytes + filesystem_mbytes
            log.info(
                'Using configured size: %d MB + %d MB calculated = %d MB',
                self.configured_size.mbytes,
                filesystem_mbytes,
                result_filesystem_mbytes
            )
            return result_filesystem_mbytes
        else:
            log.info(
                'Using configured size: %d MB',
                self.configured_size.mbytes
            )
            if self.configured_size.mbytes < filesystem_mbytes:
                log.warning(
                    '--> Configured size smaller than calculated size: %d MB',
                    filesystem_mbytes
                )
            return self.configured_size.mbytes
