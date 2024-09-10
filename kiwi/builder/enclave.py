# Copyright (c) 2024 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from typing import Dict

# project
from kiwi.defaults import Defaults
from kiwi.boot.image import BootImage
from kiwi.system.setup import SystemSetup
from kiwi.system.kernel import Kernel
from kiwi.system.result import Result
from kiwi.runtime_config import RuntimeConfig
from kiwi.xml_state import XMLState
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiEnclaveFormatError,
    KiwiEnclaveBootImageError
)

log = logging.getLogger('kiwi')


class EnclaveBuilder:
    """
    **Enclave Builder**

    Enclaves defines initrd-only image types.

    :param object xml_state: instance of :class:`XMLState`
    :param str target_dir: target directory path name
    :param str root_dir: system image root directory
    :param dict custom_args: Custom processing arguments defined as hash keys:
        * signing_keys: list of package signing keys
        * xz_options: string of XZ compression parameters
    """
    def __init__(
        self, xml_state: XMLState, target_dir: str,
        root_dir: str, custom_args: Dict = None
    ):
        self.target_dir = target_dir
        self.custom_cmdline = xml_state.build_type.get_kernelcmdline()
        self.format = xml_state.build_type.get_enclave_format()

        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=root_dir
        )
        xml_state.build_type.set_initrd_system('kiwi')
        xml_state.build_type.set_boot(f'{root_dir}/image')

        self.boot_signing_keys = custom_args['signing_keys'] if custom_args \
            and 'signing_keys' in custom_args else None

        self.xz_options = custom_args['xz_options'] if custom_args \
            and 'xz_options' in custom_args else None

        self.boot_image_task = BootImage.new(
            xml_state, target_dir, root_dir,
            signing_keys=self.boot_signing_keys
        )
        # Force BootImageKiwi instance to use existing root_dir
        self.boot_image_task.boot_root_directory = root_dir

        self.bundle_format = xml_state.get_build_type_bundle_format()
        self.image_name = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + Defaults.get_platform_name(),
                '-' + xml_state.get_image_version()
            ]
        )
        self.image: str = ''
        self.initrd: str = ''
        self.kernel_filename: str = ''
        self.enclave: str = ''
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

    def create(self) -> Result:
        """
        Build an eif image using the eif-cli

        Image types which triggers this builder are:

        * image="enclave"

        :return: result

        :rtype: instance of :class:`Result`
        """
        if not self.format:
            raise KiwiEnclaveFormatError(
                'No enclave_format= specified in build type'
            )

        # Create initrd
        self.boot_image_task.create_initrd()

        # extract kernel from boot system
        kernel = Kernel(self.boot_image_task.boot_root_directory)
        kernel_data = kernel.get_kernel()
        if kernel_data:
            self.kernel_filename = ''.join(
                [
                    os.path.basename(self.image_name), '-',
                    kernel_data.version, '.kernel'
                ]
            )
            kernel.copy_kernel(
                self.target_dir, self.kernel_filename
            )
        else:
            raise KiwiEnclaveBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image_task.boot_root_directory
            )

        self.initrd = os.path.basename(self.boot_image_task.initrd_filename)

        if self.format == 'aws-nitro':
            self.enclave = self.image_name + ".eif"
            Command.run(
                [
                    'eif_build',
                    '--kernel', '/'.join([self.target_dir, self.kernel_filename]),
                    '--ramdisk', '/'.join([self.target_dir, self.initrd]),
                    '--cmdline', self.custom_cmdline,
                    '--output', self.enclave
                ]
            )

        Result.verify_image_size(
            self.runtime_config.get_max_size_constraint(),
            self.initrd
        )
        # store image bundle_format in result
        if self.bundle_format:
            self.result.add_bundle_format(self.bundle_format)

        self.result.add(
            key='enclave',
            filename=self.enclave,
            use_for_bundle=True,
            compress=self.runtime_config.get_bundle_compression(
                default=False
            ),
            shasum=True
        )

        # create image root metadata
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
