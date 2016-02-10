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
from internal_boot_image_task import BootImageTask
from filesystem_builder import FileSystemBuilder
from compress import Compress
from checksum import Checksum
from system_setup import SystemSetup
from kernel import Kernel
from logger import log
from result import Result

from exceptions import (
    KiwiPxeBootImageError
)


class PxeBuilder(object):
    """
        Filesystem based PXE image builder. This results in creating
        a boot image(initrd) plus its appropriate kernel files and the
        root filesystem image with a checksum. The result can be used
        within the kiwi PXE boot infrastructure
    """
    def __init__(self, xml_state, target_dir, root_dir):
        self.target_dir = target_dir
        self.compressed = xml_state.build_type.get_compressed()
        self.image_name = xml_state.xml_data.get_name()
        self.machine = xml_state.get_build_type_machine_section()
        self.pxedeploy = xml_state.get_build_type_pxedeploy_section()
        self.filesystem = FileSystemBuilder(
            xml_state, target_dir, root_dir
        )
        self.system_setup = SystemSetup(
            xml_state=xml_state, description_dir=None, root_dir=root_dir
        )
        self.boot_image_task = BootImageTask(
            xml_state, target_dir
        )
        self.kernel_filename = None
        self.hypervisor_filename = None
        self.result = Result()

    def create(self):
        if not self.boot_image_task.required():
            raise KiwiPxeBootImageError(
                'pxe images requires a boot setup in the type definition'
            )
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
                [self.image_name, '-', kernel_data.version, '.kernel']
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
                    [self.image_name, '-', kernel_data.name]
                )
                kernel.copy_xen_hypervisor(
                    self.target_dir, self.hypervisor_filename
                )
                self.result.add(
                    'xen_hypervisor', self.hypervisor_filename
                )
            else:
                raise KiwiPxeBootImageError(
                    'No hypervisor in boot image tree %s found' %
                    self.boot_image_task.boot_root_directory
                )

        # create initrd for pxe boot
        self.boot_image_task.create_initrd()
        self.result.add(
            'kernel', self.kernel_filename
        )
        self.result.add(
            'initrd', self.boot_image_task.initrd_filename
        )
        self.result.add(
            'filesystem_image', self.image
        )
        self.result.add(
            'filesystem_md5', self.filesystem_checksum
        )

        if self.pxedeploy:
            log.warning(
                'Creation of client config file from pxedeploy not implemented'
            )

        return self.result
