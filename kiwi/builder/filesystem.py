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
from kiwi.filesystem import FileSystem
from kiwi.filesystem.setup import FileSystemSetup
from kiwi.storage.loop_device import LoopDevice
from kiwi.storage.device_provider import DeviceProvider
from kiwi.system.setup import SystemSetup
from kiwi.defaults import Defaults
from kiwi.logger import log
from kiwi.system.result import Result
from kiwi.runtime_config import RuntimeConfig

from kiwi.exceptions import (
    KiwiFileSystemSetupError
)


class FileSystemBuilder(object):
    """
    **Filesystem image builder**

    :param str label: filesystem label
    :param str root_dir: root directory path name
    :param str target_dir: target directory path name
    :param str requested_image_type: configured image type
    :param str requested_filesystem: requested filesystem name
    :param obejct system_setup: instance of :class:`SystemSetup`
    :param str filename: file name of the filesystem image
    :param int blocksize: configured disk blocksize
    :param object filesystem_setup: instance of :class:`FileSystemSetup`
    :param object filesystems_no_device_node: List of filesystems which are
        created from a data tree and do not require a block device e.g loop
    :param dict filesystem_custom_parameters: Configured custom filesystem
        mount and creation arguments
    :param object result: instance of :class:`Result`
    """
    def __init__(self, xml_state, target_dir, root_dir):
        self.label = None
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.requested_image_type = xml_state.get_build_type_name()
        if self.requested_image_type == 'pxe':
            self.requested_filesystem = xml_state.build_type.get_filesystem()
        else:
            self.requested_filesystem = self.requested_image_type
        if not self.requested_filesystem:
            raise KiwiFileSystemSetupError(
                'No filesystem configured in %s type' %
                self.requested_image_type
            )
        self.filesystem_custom_parameters = {
            'mount_options': xml_state.get_fs_mount_option_list()
        }
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.filename = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + xml_state.get_image_version(),
                '.', self.requested_filesystem
            ]
        )
        self.blocksize = xml_state.build_type.get_target_blocksize()
        self.filesystem_setup = FileSystemSetup(xml_state, root_dir)
        self.filesystems_no_device_node = [
            'squashfs'
        ]
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

    def create(self):
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
        self.result.verify_image_size(
            self.runtime_config.get_max_size_constraint(),
            self.filename
        )
        self.result.add(
            key='filesystem_image',
            filename=self.filename,
            use_for_bundle=True,
            compress=True,
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
            key='image_verified',
            filename=self.system_setup.export_package_verification(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        return self.result

    def _operate_on_loop(self):
        filesystem = None
        loop_provider = LoopDevice(
            self.filename,
            self.filesystem_setup.get_size_mbytes(),
            self.blocksize
        )
        loop_provider.create()
        filesystem = FileSystem(
            self.requested_filesystem, loop_provider,
            self.root_dir, self.filesystem_custom_parameters
        )
        filesystem.create_on_device(self.label)
        log.info(
            '--> Syncing data to filesystem on %s', loop_provider.get_device()
        )
        filesystem.sync_data(
            Defaults.get_exclude_list_for_root_data_sync()
        )

    def _operate_on_file(self):
        default_provider = DeviceProvider()
        filesystem = FileSystem(
            self.requested_filesystem, default_provider,
            self.root_dir, self.filesystem_custom_parameters
        )
        filesystem.create_on_file(
            self.filename, self.label,
            Defaults.get_exclude_list_for_root_data_sync()
        )
