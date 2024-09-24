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
import logging
import os
from typing import Dict

# project
from kiwi.filesystem import FileSystem
from kiwi.filesystem.setup import FileSystemSetup
from kiwi.storage.loop_device import LoopDevice
from kiwi.storage.device_provider import DeviceProvider
from kiwi.system.setup import SystemSetup
from kiwi.defaults import Defaults
from kiwi.system.result import Result
from kiwi.runtime_config import RuntimeConfig
from kiwi.xml_state import XMLState

from kiwi.exceptions import (
    KiwiFileSystemSetupError
)

log = logging.getLogger('kiwi')


class FileSystemBuilder:
    """
    **Filesystem image builder**

    :param obsject xml_state: Instance of :class:`XMLState`
    :param str target_dir: target directory path name
    :param str root_dir: root directory path name
    :param dict custom_args: Custom processing arguments defined as hash keys:
        * None
    """
    def __init__(
        self, xml_state: XMLState, target_dir: str,
        root_dir: str, custom_args: Dict = None
    ):
        self.label = None
        self.root_uuid = ''
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.bundle_format = xml_state.get_build_type_bundle_format()
        self.requested_image_type = xml_state.get_build_type_name()
        if self.requested_image_type in Defaults.get_kis_image_types():
            self.requested_filesystem = xml_state.build_type.get_filesystem()
        else:
            self.requested_filesystem = self.requested_image_type
        if not self.requested_filesystem:
            raise KiwiFileSystemSetupError(
                'No filesystem configured in %s type' %
                self.requested_image_type
            )
        self.filesystem_custom_parameters = {
            'mount_options': xml_state.get_fs_mount_option_list(),
            'create_options': xml_state.get_fs_create_option_list()
        }
        if self.requested_filesystem == 'squashfs':
            self.filesystem_custom_parameters['compression'] = \
                xml_state.build_type.get_squashfscompression()
        elif self.requested_filesystem == 'erofs':
            self.filesystem_custom_parameters['compression'] = \
                xml_state.build_type.get_erofscompression()

        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.filename = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + Defaults.get_platform_name(),
                '-' + xml_state.get_image_version(),
                '.', self.requested_filesystem
            ]
        )
        self.blocksize = xml_state.build_type.get_target_blocksize()
        self.filesystem_setup = FileSystemSetup(xml_state, root_dir)
        self.filesystems_no_device_node = [
            'squashfs', 'erofs'
        ]
        self.luks = xml_state.get_luks_credentials()
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

    def create(self) -> Result:
        """
        Build a mountable filesystem image

        Image types which triggers this builder are:

        * image="ext2"
        * image="ext3"
        * image="ext4"
        * image="btrfs"
        * image="xfs"

        :return: result

        :rtype: instance of :class:`Result`
        """
        log.info(
            'Creating %s filesystem', self.requested_filesystem
        )
        supported_filesystems = Defaults.get_filesystem_image_types()
        if self.requested_filesystem not in supported_filesystems:
            raise KiwiFileSystemSetupError(
                'Unknown filesystem: %s' % self.requested_filesystem
            )
        if self.requested_filesystem not in self.filesystems_no_device_node:
            self._operate_on_loop()
        else:
            self._operate_on_file()
        Result.verify_image_size(
            self.runtime_config.get_max_size_constraint(),
            self.filename
        )
        if self.bundle_format:
            self.result.add_bundle_format(self.bundle_format)
        compression = self.runtime_config.get_bundle_compression(default=True)
        if self.luks is not None:
            compression = False
        self.result.add(
            key='filesystem_image',
            filename=self.filename,
            use_for_bundle=True,
            compress=compression,
            shasum=True
        )
        self.result.add(
            key='image_packages',
            filename=self.system_setup.export_package_list(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        self.result.add(
            key='image_changes',
            filename=self.system_setup.export_package_changes(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=True,
            shasum=False
        )
        self.result.add(
            key='image_verified',
            filename=self.system_setup.export_package_verification(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        return self.result

    def _operate_on_loop(self) -> None:
        with LoopDevice(
            self.filename,
            self.filesystem_setup.get_size_mbytes(),
            self.blocksize
        ) as loop_provider:
            loop_provider.create()
            with FileSystem.new(
                self.requested_filesystem, loop_provider,
                self.root_dir + os.sep, self.filesystem_custom_parameters
            ) as filesystem:
                filesystem.create_on_device(self.label)
                self.root_uuid = loop_provider.get_uuid(
                    loop_provider.get_device()
                )
                log.info(
                    '--> Syncing data to filesystem on {0}'.format(
                        loop_provider.get_device()
                    )
                )
                filesystem.sync_data(
                    Defaults.
                    get_exclude_list_for_root_data_sync() + Defaults.
                    get_exclude_list_from_custom_exclude_files(self.root_dir)
                )

    def _operate_on_file(self) -> None:
        default_provider = DeviceProvider()
        with FileSystem.new(
            self.requested_filesystem, default_provider,
            self.root_dir, self.filesystem_custom_parameters
        ) as filesystem:
            filesystem.create_on_file(
                self.filename, self.label,
                Defaults.get_exclude_list_for_root_data_sync() + Defaults.
                get_exclude_list_from_custom_exclude_files(self.root_dir)
            )
