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
import platform
from collections import OrderedDict

from ...exceptions import (
    KiwiFormatSetupError
)

from ...defaults import Defaults
from ...path import Path
from ...logger import log


class DiskFormatBase(object):
    """
    Base class to create disk formats from a raw disk image

    Attributes

    * :attr:`xml_state`
        Instance of XMLState

    * :attr:`root_dir`
        root directory path name

    * :attr:`arch`
        platform.machine

    * :attr:`target_dir`
        target directory path name

    * :attr:`custom_args`
        list of custom format options

    * :attr:`temp_image_dir`
        temporary manifest directory

    * :attr:`diskname`
        raw disk file path name

    * :attr:`image_format`
        disk format name
    """
    def __init__(self, xml_state, root_dir, target_dir, custom_args=None):
        self.xml_state = xml_state
        self.root_dir = root_dir
        self.arch = platform.machine()
        self.target_dir = target_dir
        self.custom_args = {}
        self.temp_image_dir = None
        self.image_format = None
        self.diskname = self.get_target_name_for_format('raw')

        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Implementation in specialized disk format class if required

        :param list custom_args: unused
        """
        pass

    def create_image_format(self):
        """
        Create disk format

        Implementation in specialized disk format class required
        """
        raise NotImplementedError

    def get_qemu_option_list(self, custom_args):
        """
        Create list of qemu options from custom_args dict

        :param dict custom_args: arguments

        :return: qemu option list
        :rtype: list
        """
        options = []
        if custom_args:
            ordered_args = OrderedDict(sorted(custom_args.items()))
            for key, value in list(ordered_args.items()):
                options.append('-o')
                options.append(key)
                if value:
                    options.append(value)
        return options

    def get_target_name_for_format(self, format_name):
        """
        Create target file path name for specified format

        :param string format_name: disk format name

        :return: file path name
        :rtype: string
        """
        if format_name != 'raw':
            if format_name not in Defaults.get_disk_format_types():
                raise KiwiFormatSetupError(
                    'unsupported disk format %s' % format_name
                )
        return ''.join(
            [
                self.target_dir, '/',
                self.xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + self.xml_state.get_image_version(),
                '.' + format_name
            ]
        )

    def store_to_result(self, result):
        """
        Store result file of the format conversion into the
        provided result instance.

        By default only the converted image file will be stored.
        Subformats which creates additional metadata files needs
        to overwrite this method

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.get_target_name_for_format(
                self.image_format
            ),
            use_for_bundle=True,
            compress=False,
            shasum=True
        )

    def __del__(self):
        if self.temp_image_dir and os.path.exists(self.temp_image_dir):
            log.info('Cleaning up %s instance', type(self).__name__)
            Path.wipe(self.temp_image_dir)
