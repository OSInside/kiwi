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
from typing import Dict

# project
from kiwi.defaults import Defaults
from kiwi.boot.image import BootImage
from kiwi.builder.filesystem import FileSystemBuilder
from kiwi.utils.compress import Compress
from kiwi.utils.checksum import Checksum
from kiwi.system.setup import SystemSetup
from kiwi.system.kernel import Kernel
from kiwi.system.result import Result
from kiwi.runtime_config import RuntimeConfig
from kiwi.archive.tar import ArchiveTar
from kiwi.xml_state import XMLState

from kiwi.exceptions import (
    KiwiKisBootImageError
)

log = logging.getLogger('kiwi')


class KisBuilder:
    """
    **Filesystem based image builder.**

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
        self.compressed = xml_state.build_type.get_compressed()
        self.xen_server = xml_state.is_xen_server()
        self.custom_cmdline = xml_state.build_type.get_kernelcmdline()
        self.filesystem = FileSystemBuilder(
            xml_state, target_dir, root_dir + '/'
        ) if xml_state.build_type.get_filesystem() else None
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=root_dir
        )
        self.initrd_system = xml_state.get_initrd_system()

        self.boot_signing_keys = custom_args['signing_keys'] if custom_args \
            and 'signing_keys' in custom_args else None

        self.xz_options = custom_args['xz_options'] if custom_args \
            and 'xz_options' in custom_args else None

        self.boot_image_task = BootImage.new(
            xml_state, target_dir, root_dir,
            signing_keys=self.boot_signing_keys
        )
        self.image_name = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + Defaults.get_platform_name(),
                '-' + xml_state.get_image_version()
            ]
        )
        self.image: str = ''
        self.append_file = ''.join([self.image_name, '.append'])
        self.archive_name = ''.join([self.image_name, '.tar'])
        self.checksum_name = ''.join([self.image_name, '.md5'])
        self.kernel_filename: str = ''
        self.hypervisor_filename: str = ''
        self.result = Result(xml_state)
        self.runtime_config = RuntimeConfig()

        if not self.boot_image_task.has_initrd_support():
            log.warning('Building without initrd support !')

    def create(self) -> Result:
        """
        Build a component image consisting out of a boot image(initrd)
        plus its appropriate kernel files and the root filesystem
        image with a checksum.

        Image types which triggers this builder are:

        * image="kis"
        * image="pxe"

        :raises KiwiKisBootImageError: if no kernel or hipervisor is found
            in boot image tree
        :return: result

        :rtype: instance of :class:`Result`
        """
        if self.filesystem:
            log.info('Creating root filesystem image')
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

            log.info('Creating root filesystem MD5 checksum')
            checksum = Checksum(self.image)
            checksum.md5(self.checksum_name)

        # prepare initrd
        if self.boot_image_task.has_initrd_support():
            log.info('Creating boot image')
            self.boot_image_task.prepare()

        # export modprobe configuration to boot image
        self.system_setup.export_modprobe_setup(
            self.boot_image_task.boot_root_directory
        )

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
            raise KiwiKisBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image_task.boot_root_directory
            )

        # extract hypervisor from boot(initrd) root system
        if self.xen_server:
            hypervisor_data = kernel.get_xen_hypervisor()
            if hypervisor_data:
                self.hypervisor_filename = ''.join(
                    [
                        os.path.basename(self.image_name),
                        '-', hypervisor_data.name
                    ]
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
                raise KiwiKisBootImageError(
                    'No hypervisor in boot image tree %s found' %
                    self.boot_image_task.boot_root_directory
                )

        # create initrd
        if self.boot_image_task.has_initrd_support():
            self.boot_image_task.create_initrd()

        # create append information
        # this information helps to configure the deployment infrastructure
        if self.filesystem and self.filesystem.root_uuid \
           and self.initrd_system == 'dracut':
            cmdline = 'root=UUID={}'.format(self.filesystem.root_uuid)
            if self.custom_cmdline:
                cmdline += ' {}'.format(self.custom_cmdline)
            with open(self.append_file, 'w') as append:
                append.write(cmdline)

        # put results into a tarball
        if not self.xz_options:
            self.xz_options = Defaults.get_xz_compression_options()

        kis_tarball_files = [
            self.kernel_filename,
            os.path.basename(self.checksum_name),
        ]
        if self.boot_image_task.initrd_filename:
            kis_tarball_files.append(
                os.path.basename(self.boot_image_task.initrd_filename)
            )

        if self.image:
            kis_tarball_files.append(os.path.basename(self.image))

        if self.filesystem and self.filesystem.root_uuid \
           and self.initrd_system == 'dracut':
            kis_tarball_files.append(os.path.basename(self.append_file))

        kis_tarball = ArchiveTar(
            self.archive_name,
            create_from_file_list=True,
            file_list=kis_tarball_files
        )

        if self.compressed:
            self.archive_name = kis_tarball.create(self.target_dir)
        else:
            self.archive_name = kis_tarball.create_xz_compressed(
                self.target_dir, xz_options=self.xz_options
            )

        Result.verify_image_size(
            self.runtime_config.get_max_size_constraint(),
            self.archive_name
        )
        # store results
        self.result.add(
            key='kis_archive',
            filename=self.archive_name,
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
