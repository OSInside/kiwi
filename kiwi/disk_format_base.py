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

from exceptions import (
    KiwiFormatSetupError
)

from defaults import Defaults


class DiskFormatBase(object):
    """
        base class to create disk formats from a raw disk image
    """
    def __init__(self, xml_state, source_dir, target_dir, custom_args=None):
        self.xml_state = xml_state
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.custom_args = {}
        self.diskname = self.get_target_name_for_format('raw')

        self.post_init(custom_args)

    def post_init(self, custom_args):
        # overwrite in specialized format class when needed
        pass

    def create_image_format(self):
        raise NotImplementedError

    def get_target_name_for_format(self, format_name):
        if format_name != 'raw':
            if format_name not in Defaults.get_disk_format_types():
                raise KiwiFormatSetupError(
                    'unsupported disk format %s' % format_name
                )
        return ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(), '.' + format_name
            ]
        )
