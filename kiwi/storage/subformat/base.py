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
from collections import OrderedDict

# project
from kiwi.command import Command
from kiwi.runtime_config import RuntimeConfig
from kiwi.defaults import Defaults
from kiwi.path import Path

from kiwi.exceptions import (
    KiwiFormatSetupError,
    KiwiResizeRawDiskError
)

log = logging.getLogger('kiwi')


class DiskFormatBase:
    """
    **Base class to create disk formats from a raw disk image**

    :param object xml_state: Instance of XMLState
    :param string root_dir: root directory path name
    :param string arch: Defaults.get_platform_name
    :param string target_dir: target directory path name
    :param dict custom_args: custom format options dictionary
    """
    def __init__(self, xml_state, root_dir, target_dir, custom_args=None):
        self.xml_state = xml_state
        self.root_dir = root_dir
        self.arch = Defaults.get_platform_name()
        self.target_dir = target_dir
        self.custom_args = {}
        self.temp_image_dir = None
        self.image_format = None
        self.diskname = self.get_target_file_path_for_format('raw')
        self.runtime_config = RuntimeConfig()

        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Implementation in specialized disk format class if required

        :param list custom_args: unused
        """
        pass

    def has_raw_disk(self):
        """
        Check if the base raw disk image exists

        :return: True or False

        :rtype: bool
        """
        return os.path.exists(self.diskname)

    def resize_raw_disk(self, size_bytes, append=False):
        """
        Resize raw disk image to specified size. If the request
        would actually shrink the disk an exception is raised.
        If the disk got changed the method returns True, if
        the new size is the same as the current size nothing
        gets resized and the method returns False

        :param int size: size in bytes

        :return: True or False

        :rtype: bool
        """
        if not append:
            current_byte_size = os.path.getsize(self.diskname)
            size_bytes = int(size_bytes)
            if size_bytes < current_byte_size:
                raise KiwiResizeRawDiskError(
                    'shrinking {0} disk to {1} bytes corrupts the image'.format(
                        self.diskname, size_bytes
                    )
                )
            elif size_bytes == current_byte_size:
                return False
        Command.run(
            [
                'qemu-img', 'resize', self.diskname,
                '+{0}'.format(size_bytes) if append else format(size_bytes)
            ]
        )
        return True

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
                if key == 'adapter_type=pvscsi':
                    # qemu does not support the pvscsi type:
                    # To build a vmdk image with ddb.adapterType set to
                    # pvscsi we need to manually change the header but
                    # have to create a vmdk with lsilogic as scsi adapter
                    # first. I don't really like this hack but it seems
                    # there is no way around. For details see
                    # bsc#1099569
                    key = 'adapter_type=lsilogic'
                options.append('-o')
                if value:
                    options.append('{0}={1}'.format(key, value))
                else:
                    options.append(key)
        return options

    def get_target_file_path_for_format(self, format_name):
        """
        Create target file path name for specified format

        :param string format_name: disk format name

        :return: file path name

        :rtype: str
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

        By default only the converted image file will be stored
        as compressed file. Subformats which creates additional
        metadata files or want to use other result flags needs
        to overwrite this method

        :param object result: Instance of Result
        """
        result.add(
            key='disk_format_image',
            filename=self.get_target_file_path_for_format(
                self.image_format
            ),
            use_for_bundle=True,
            compress=self.runtime_config.get_bundle_compression(
                default=True
            ),
            shasum=True
        )

    def __del__(self):
        if self.temp_image_dir and os.path.exists(self.temp_image_dir):
            log.info('Cleaning up %s instance', type(self).__name__)
            Path.wipe(self.temp_image_dir)
