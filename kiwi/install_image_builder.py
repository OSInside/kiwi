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
from tempfile import mkdtemp
import os

# project
from command import Command
from bootloader_config import BootLoaderConfig
from filesystem_squashfs import FileSystemSquashFs
from image_identifier import ImageIdentifier
from path import Path
from checksum import Checksum
from logger import log
from kernel import Kernel

from exceptions import (
    KiwiInstallBootImageError
)


class InstallImageBuilder(object):
    """
        Installation image builder
    """
    def __init__(
        self, xml_state, target_dir, disk_image, boot_image_task
    ):
        self.target_dir = target_dir
        self.disk_image = disk_image
        self.boot_image_task = boot_image_task
        self.xml_state = xml_state
        self.mbrid = ImageIdentifier()
        self.mbrid.calculate_id()
        self.media_dir = None

    def create_install_iso(self):
        """
            Create an install ISO from the disk_image as hybrid ISO
            bootable via legacy BIOS, EFI and as disk from Stick
        """
        self.media_dir = mkdtemp(
            prefix='install-media.', dir=self.target_dir
        )
        # the install image transfer is checked against a checksum
        log.info('Creating disk image checksum')
        checksum = Checksum(self.disk_image)
        checksum.md5(
            self.boot_image_task.boot_root_directory + '/etc/image.md5'
        )

        # the kiwi initrd code triggers the install by trigger files
        self.__create_iso_install_trigger_files()

        # the install image is stored as squashfs embedded file
        log.info('Creating squashfs embedded disk image')
        squashed_image_file = self.disk_image + '.squashfs'
        squashed_image = FileSystemSquashFs(
            device_provider=None, source_dir=self.disk_image
        )
        squashed_image.create_on_file(squashed_image_file)
        Command.run(
            ['mv', squashed_image_file, self.media_dir]
        )

        # setup bootloader config to boot the ISO via EFI
        self.bootloader_config_grub = BootLoaderConfig.new(
            'grub2', self.xml_state, self.media_dir
        )
        self.bootloader_config_grub.setup_install_boot_images(
            mbrid=self.mbrid,
            lookup_path=self.boot_image_task.boot_root_directory
        )
        self.bootloader_config_grub.setup_install_image_config(
            self.mbrid
        )
        self.bootloader_config_grub.write()

        # setup bootloader config to boot the ISO via isolinux
        # TODO

        self.__create_iso_install_kernel_and_initrd()

        # TODO
        # create iso filesystem from self.media_dir and make it hybrid

    def create_install_pxe_archive(self):
        # TODO
        pass

    def __create_iso_install_kernel_and_initrd(self):
        boot_path = self.media_dir + '/boot/x86_64/loader'
        Path.create(boot_path)
        kernel = Kernel(self.boot_image_task.boot_root_directory)
        if kernel.get_kernel():
            kernel.copy_kernel(boot_path, '/linux')
        else:
            raise KiwiInstallBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image_task.boot_root_directory
            )
        # TODO: for xen dom0 boot the hypervisor needs to be copied too
        self.boot_image_task.create_initrd(self.mbrid)
        Command.run(
            [
                'mv', self.boot_image_task.initrd_filename,
                boot_path + '/initrd'
            ]
        )

    def __create_iso_install_trigger_files(self):
        diskname = os.path.basename(self.disk_image)
        initrd_trigger = \
            self.boot_image_task.boot_root_directory + '/config.vmxsystem'
        iso_trigger = self.media_dir + '/config.isoclient'
        with open(initrd_trigger, 'w') as vmx_system:
            vmx_system.write('IMAGE="%s"\n' % diskname)
        with open(iso_trigger, 'w') as iso_system:
            iso_system.write('IMAGE="%s"\n' % diskname)

    def __del__(self):
        # if self.media_dir:
        #    Path.wipe(self.media_dir)
        pass
