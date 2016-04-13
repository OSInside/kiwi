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
from ..boot.image import BootImage
from .filesystem import FileSystemBuilder
from ..utils.compress import Compress
from ..utils.checksum import Checksum
from ..system.setup import SystemSetup
from ..system.kernel import Kernel
from ..logger import log
from ..system.result import Result

from ..exceptions import (
    KiwiPxeBootImageError
)


class PxeBuilder(object):
    """
    Filesystem based PXE image builder.

    Attributes

    * :attr:`target_dir`
        target directory path name

    * :attr:`compressed`
        Request to XZ compress filesystem image

    * :attr:`machine`
        Configured build type machine section

    * :attr:`pxedeploy`
        Configured build type pxedeploy section

    * :attr:`filesystem`
        Instance of FileSystemBuilder

    * :attr:`system_setup`
        Instance of SystemSetup

    * :attr:`boot_image_task`
        Instance of BootImage

    * :attr:`image_name`
        File name of the filesystem image

    * :attr:`kernel_filename`
        File name of the kernel image

    * :attr:`hypervisor_filename`
        File name of the hypervisor image

    * :attr:`result`
        Instance of Result
    """
    def __init__(self, xml_state, target_dir, root_dir):
        self.target_dir = target_dir
        self.compressed = xml_state.build_type.get_compressed()
        self.machine = xml_state.get_build_type_machine_section()
        self.pxedeploy = xml_state.get_build_type_pxedeploy_section()
        self.filesystem = FileSystemBuilder(
            xml_state, target_dir, root_dir
        )
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=root_dir
        )
        self.boot_image_task = BootImage(
            xml_state, target_dir
        )
        self.image_name = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + xml_state.get_image_version(),
            ]
        )
        self.kernel_filename = None
        self.hypervisor_filename = None
        self.result = Result(xml_state)

    def create(self):
        """
        Build a pxe image set consisting out of a boot image(initrd)
        plus its appropriate kernel files and the root filesystem
        image with a checksum. The result can be used within the kiwi
        PXE boot infrastructure

        Image types which triggers this builder are:

        * image="pxe"
        """
        log.info('Creating PXE root filesystem image')
        self.filesystem.create()
        self.image = self.filesystem.filename
        if self.compressed:
            log.info('xz compressing root filesystem image')
            compress = Compress(self.image)
            compress.xz()
            self.image = compress.compressed_filename

        log.info('Creating PXE root filesystem MD5 checksum')
        self.filesystem_checksum = self.filesystem.filename + '.md5'
        checksum = Checksum(self.image)
        checksum.md5(self.filesystem_checksum)

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
        if self.machine and self.machine.get_domain() == 'dom0':
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

        # store results
        self.result.add(
            key='kernel',
            filename=self.target_dir + '/' + self.kernel_filename,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
        self.result.add(
            key='initrd',
            filename=self.boot_image_task.initrd_filename,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
        self.result.add(
            key='filesystem_image',
            filename=self.image,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
        self.result.add(
            key='filesystem_md5',
            filename=self.filesystem_checksum,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )

        # create image root metadata
        self.result.add(
            key='image_packages',
            filename=self.system_setup.export_rpm_package_list(
                self.target_dir
            ),
            use_for_bundle=True,
            compress=False,
            shasum=False
        )
        self.result.add(
            key='image_verified',
            filename=self.system_setup.export_rpm_package_verification(
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
