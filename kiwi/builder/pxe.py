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

# project
from kiwi.defaults import Defaults
from kiwi.command import Command
from kiwi.boot.image import BootImage
from kiwi.builder.filesystem import FileSystemBuilder
from kiwi.utils.compress import Compress
from kiwi.utils.checksum import Checksum
from kiwi.system.setup import SystemSetup
from kiwi.system.kernel import Kernel
from kiwi.logger import log
from kiwi.system.result import Result
from kiwi.runtime_config import RuntimeConfig

from kiwi.exceptions import (
    KiwiPxeBootImageError
)


class PxeBuilder(object):
    """
    **Filesystem based PXE image builder.**

    :param object xml_state: instance of :class:`XMLState`
    :param str target_dir: target directory path name
    :param str root_dir: system image root directory
    :param dict custom_args: Custom processing arguments defined as hash keys:
        * signing_keys: list of package signing keys
        * xz_options: string of XZ compression parameters
    """
    def __init__(self, xml_state, target_dir, root_dir, custom_args=None):
        self.target_dir = target_dir
        self.compressed = xml_state.build_type.get_compressed()
        self.xen_server = xml_state.is_xen_server()
        self.pxedeploy = xml_state.get_build_type_pxedeploy_section()
        self.filesystem = FileSystemBuilder(
            xml_state, target_dir, root_dir + '/'
        )
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=root_dir
        )

        self.boot_signing_keys = custom_args['signing_keys'] if custom_args \
            and 'signing_keys' in custom_args else None

        self.xz_options = custom_args['xz_options'] if custom_args \
            and 'xz_options' in custom_args else None

        self.boot_image_task = BootImage(
            xml_state, target_dir, signing_keys=self.boot_signing_keys
        )
        self.image_name = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + xml_state.get_image_version()
            ]
        )
        self.archive_name = ''.join([self.image_name, '.tar.xz'])
        self.checksum_name = ''.join([self.image_name, '.md5'])
        self.kernel_filename = None
        self.hypervisor_filename = None
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

    def create(self):
        """
        Build a pxe image set consisting out of a boot image(initrd)
        plus its appropriate kernel files and the root filesystem
        image with a checksum. The result can be used within the kiwi
        PXE boot infrastructure

        Image types which triggers this builder are:

        * image="pxe"

        :raises KiwiPxeBootImageError: if no kernel or hipervisor is found
            in boot image tree
        :return: result

        :rtype: instance of :class:`Result`
        """
        log.info('Creating PXE root filesystem image')
        self.filesystem.create()
        os.rename(
            self.filesystem.filename, self.image_name
        )
        self.image = self.image_name
        if self.compressed:
            log.info('xz compressing root filesystem image')
            compress = Compress(self.image)
            compress.xz(self.xz_options)
            self.image = compress.compressed_filename

        log.info('Creating PXE root filesystem MD5 checksum')
        checksum = Checksum(self.image)
        checksum.md5(self.checksum_name)

        # prepare boot(initrd) root system
        log.info('Creating PXE boot image')
        self.boot_image_task.prepare()

        # export modprobe configuration to boot image
        self.system_setup.export_modprobe_setup(
            self.boot_image_task.boot_root_directory
        )

        # extract kernel from boot(initrd) root system
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
            raise KiwiPxeBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image_task.boot_root_directory
            )

        # extract hypervisor from boot(initrd) root system
        if self.xen_server:
            kernel_data = kernel.get_xen_hypervisor()
            if kernel_data:
                self.hypervisor_filename = ''.join(
                    [os.path.basename(self.image_name), '-', kernel_data.name]
                )
                kernel.copy_xen_hypervisor(
                    self.target_dir, self.hypervisor_filename
                )
                self.result.add(
                    key='xen_hypervisor',
                    filename=self.target_dir + '/' + self.hypervisor_filename,
                    use_for_bundle=True,
                    compress=False,
                    shasum=True
                )
            else:
                raise KiwiPxeBootImageError(
                    'No hypervisor in boot image tree %s found' %
                    self.boot_image_task.boot_root_directory
                )

        # create initrd for pxe boot
        self.boot_image_task.create_initrd()

        # put results into a tarball
        if not self.xz_options:
            self.xz_options = Defaults.get_xz_compression_options()
        bash_command = [
            'tar', '-C', self.target_dir, '-c', '--to-stdout'
        ] + [
            self.kernel_filename,
            os.path.basename(self.boot_image_task.initrd_filename),
            os.path.basename(self.image),
            os.path.basename(self.checksum_name)
        ] + [
            '|', 'xz', '-f'
        ] + self.xz_options + [
            '>', self.archive_name
        ]
        Command.run(['bash', '-c', ' '.join(bash_command)])

        self.result.verify_image_size(
            self.runtime_config.get_max_size_constraint(),
            self.archive_name
        )
        # store results
        self.result.add(
            key='pxe_archive',
            filename=self.archive_name,
            use_for_bundle=True,
            compress=False,
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
            key='image_verified',
            filename=self.system_setup.export_package_verification(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )

        if self.pxedeploy:
            log.warning(
                'Creation of client config file from pxedeploy not implemented'
            )

        return self.result
