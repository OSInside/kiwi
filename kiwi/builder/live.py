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
import platform
import shutil

# project
from kiwi.bootloader.config import BootLoaderConfig
from kiwi.filesystem import FileSystem
from kiwi.filesystem.isofs import FileSystemIsoFs
from kiwi.boot.image import BootImage
from kiwi.system.size import SystemSize
from kiwi.system.setup import SystemSetup
from kiwi.firmware import FirmWare
from kiwi.defaults import Defaults
from kiwi.path import Path
from kiwi.system.result import Result
from kiwi.iso import Iso
from kiwi.system.identifier import SystemIdentifier
from kiwi.system.kernel import Kernel
from kiwi.command import Command
from kiwi.logger import log

from kiwi.exceptions import (
    KiwiLiveBootImageError
)


class LiveImageBuilder(object):
    """
    Live image builder

    Attributes

    * :attr:`media_dir`
        Temporary directory to collect the install ISO contents

    * :attr:`arch`
        platform.machine

    * :attr:`root_dir`
        root directory path name

    * :attr:`target_dir`
        target directory path name

    * :attr:`xml_state`
        Instance of XMLState

    * :attr:`live_type`
        Configured live ISO type name

    * :attr:`types`
        List of supported live ISO types

    * :attr:`hybrid`
        Request for hybrid ISO: true|false

    * :attr:`volume_id`
        Configured ISO volume ID or default

    * :attr:`mbrid`
        Instance of SystemIdentifier

    * :attr:`filesystem_custom_parameters`
        Configured custom filesystem mount and creation arguments

    * :attr:`boot_image_task`
        Instance of BootImage

    * :attr:`firmware`
        Instance of FirmWare

    * :attr:`system_setup`
        Instance of SystemSetup

    * :attr:`isoname`
        File name of the live ISO image

    * :attr:`live_image_file`
        File name of compressed image on the ISO

    * :attr:`result`
        Instance of Result
    """
    def __init__(self, xml_state, target_dir, root_dir):
        self.media_dir = None
        self.arch = platform.machine()
        if self.arch == 'i686' or self.arch == 'i586':
            self.arch = 'ix86'
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.xml_state = xml_state
        self.live_type = xml_state.build_type.get_flags()
        self.types = Defaults.get_live_iso_types()
        self.hybrid = xml_state.build_type.get_hybrid()
        self.volume_id = xml_state.build_type.get_volid()
        self.machine = xml_state.get_build_type_machine_section()
        self.mbrid = SystemIdentifier()
        self.mbrid.calculate_id()
        self.filesystem_custom_parameters = {
            'mount_options': xml_state.get_fs_mount_option_list()
        }

        if not self.live_type:
            self.live_type = Defaults.get_default_live_iso_type()

        self.boot_image_task = BootImage(
            xml_state, target_dir
        )
        self.firmware = FirmWare(
            xml_state
        )
        self.system_setup = SystemSetup(
            xml_state=xml_state, root_dir=self.root_dir
        )
        self.isoname = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + platform.machine(),
                '-' + xml_state.get_image_version(),
                '.iso'
            ]
        )
        self.live_image_file = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '-read-only.', self.arch, '-',
                xml_state.get_image_version()
            ]
        )
        self.result = Result(xml_state)

    def create(self):
        """
        Build a bootable hybrid live ISO image

        Image types which triggers this builder are:

        * image="iso"
        """
        # media dir to store CD contents
        self.media_dir = mkdtemp(
            prefix='live-media.', dir=self.target_dir
        )
        rootsize = SystemSize(self.media_dir)

        # custom iso metadata
        log.info('Using following live ISO metadata:')
        log.info('--> Application id: %s', self.mbrid.get_id())
        log.info('--> Publisher: %s', Defaults.get_publisher())
        custom_iso_args = {
            'create_options': [
                '-A', self.mbrid.get_id(),
                '-p', '"' + Defaults.get_preparer() + '"',
                '-publisher', '"' + Defaults.get_publisher() + '"'
            ]
        }
        if self.volume_id:
            log.info('--> Volume id: %s', self.volume_id)
            custom_iso_args['create_options'].append('-V')
            custom_iso_args['create_options'].append('"' + self.volume_id + '"')

        # prepare boot(initrd) root system
        log.info('Preparing live ISO boot system')
        self.boot_image_task.prepare()

        # export modprobe configuration to boot image
        self.system_setup.export_modprobe_setup(
            self.boot_image_task.boot_root_directory
        )

        # pack system into live boot structure
        log.info('Packing system into live ISO type: %s', self.live_type)
        if self.live_type in self.types:
            live_type_image = FileSystem(
                name=self.types[self.live_type],
                device_provider=None,
                root_dir=self.root_dir,
                custom_args=self.filesystem_custom_parameters
            )
            live_type_image.create_on_file(self.live_image_file)
            Command.run(
                ['mv', self.live_image_file, self.media_dir]
            )
            self._create_live_iso_client_config(self.live_type)
        else:
            raise KiwiLiveBootImageError(
                'live ISO type "%s" not supported' % self.live_type
            )

        # setup bootloader config to boot the ISO via isolinux
        log.info('Setting up isolinux bootloader configuration')
        bootloader_config_isolinux = BootLoaderConfig(
            'isolinux', self.xml_state, self.media_dir
        )
        bootloader_config_isolinux.setup_live_boot_images(
            mbrid=None,
            lookup_path=self.boot_image_task.boot_root_directory
        )
        bootloader_config_isolinux.setup_live_image_config(
            mbrid=None
        )
        bootloader_config_isolinux.write()

        # setup bootloader config to boot the ISO via EFI
        if self.firmware.efi_mode():
            log.info('Setting up EFI grub bootloader configuration')
            bootloader_config_grub = BootLoaderConfig(
                'grub2', self.xml_state, self.media_dir
            )
            bootloader_config_grub.setup_live_boot_images(
                mbrid=self.mbrid,
                lookup_path=self.boot_image_task.boot_root_directory
            )
            bootloader_config_grub.setup_live_image_config(
                mbrid=self.mbrid
            )
            bootloader_config_grub.write()
            if self.firmware.efi_mode() == 'uefi':
                # write bootloader config to EFI directory in order to allow
                # grub loaded by shim to find the config file
                shutil.copy(
                    self.media_dir + '/boot/grub2/grub.cfg',
                    self.media_dir + '/EFI/BOOT'
                )

        # create initrd for live image
        log.info('Creating live ISO boot image')
        self._create_live_iso_kernel_and_initrd()

        # calculate size and decide if we need UDF
        if rootsize.accumulate_mbyte_file_sizes() > 4096:
            log.info('ISO exceeds 4G size, using UDF filesystem')
            custom_iso_args['create_options'].append('-iso-level')
            custom_iso_args['create_options'].append('3')
            custom_iso_args['create_options'].append('-udf')

        # create iso filesystem from media_dir
        log.info('Creating live ISO image')
        iso_image = FileSystemIsoFs(
            device_provider=None,
            root_dir=self.media_dir,
            custom_args=custom_iso_args
        )
        iso_header_offset = iso_image.create_on_file(self.isoname)

        # make it hybrid
        if self.hybrid:
            Iso.create_hybrid(
                iso_header_offset, self.mbrid, self.isoname
            )

        self.result.add(
            key='live_image',
            filename=self.isoname,
            use_for_bundle=True,
            compress=False,
            shasum=True
        )
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
        return self.result

    def _create_live_iso_kernel_and_initrd(self):
        boot_path = self.media_dir + '/boot/' + self.arch + '/loader'
        Path.create(boot_path)
        kernel = Kernel(self.boot_image_task.boot_root_directory)
        if kernel.get_kernel():
            kernel.copy_kernel(boot_path, '/linux')
        else:
            raise KiwiLiveBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image_task.boot_root_directory
            )
        if self.machine and self.machine.get_domain() == 'dom0':
            if kernel.get_xen_hypervisor():
                kernel.copy_xen_hypervisor(boot_path, '/xen.gz')
            else:
                raise KiwiLiveBootImageError(
                    'No hypervisor in boot image tree %s found' %
                    self.boot_image_task.boot_root_directory
                )
        self.boot_image_task.create_initrd(self.mbrid)
        Command.run(
            [
                'mv', self.boot_image_task.initrd_filename,
                boot_path + '/initrd'
            ]
        )

    def _create_live_iso_client_config(self, iso_type):
        """
            Setup IMAGE and UNIONFS_CONFIG variables as they are used in
            the kiwi isoboot code. Variable contents:

            + IMAGE=target_device;live_iso_name_definition
            + UNIONFS_CONFIG=rw_device,ro_device,union_type

            If no real block device is used or can be predefined the
            word 'loop' is set as a placeholder or indicator to use a loop
            device. For more details please refer to the kiwi shell boot
            code
        """
        iso_client_config_file = self.media_dir + '/config.isoclient'
        iso_client_params = Defaults.get_live_iso_client_parameters()
        (system_device, union_device, union_type) = iso_client_params[iso_type]

        with open(iso_client_config_file, 'w') as config:
            config.write(
                'IMAGE="%s;%s.%s;%s"\n' % (
                    system_device,
                    self.xml_state.xml_data.get_name(), self.arch,
                    self.xml_state.get_image_version()
                )
            )
            config.write(
                'UNIONFS_CONFIG="%s,loop,%s"\n' %
                (union_device, union_type)
            )

    def __del__(self):
        if self.media_dir:
            log.info('Cleaning up %s instance', type(self).__name__)
            Path.wipe(self.media_dir)
