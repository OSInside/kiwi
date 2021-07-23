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
from typing import (
    Dict, Optional
)
import shutil

# project
from kiwi.utils.temporary import Temporary
from kiwi.command import Command
from kiwi.storage.device_provider import DeviceProvider
from kiwi.boot.image.base import BootImageBase
from kiwi.boot.image import BootImage
from kiwi.bootloader.config import BootLoaderConfig
from kiwi.filesystem.squashfs import FileSystemSquashFs
from kiwi.filesystem.isofs import FileSystemIsoFs
from kiwi.firmware import FirmWare
from kiwi.system.identifier import SystemIdentifier
from kiwi.path import Path
from kiwi.defaults import Defaults
from kiwi.utils.checksum import Checksum
from kiwi.system.kernel import Kernel
from kiwi.utils.compress import Compress
from kiwi.archive.tar import ArchiveTar
from kiwi.system.setup import SystemSetup
from kiwi.iso_tools.base import IsoToolsBase
from kiwi.xml_state import XMLState


from kiwi.exceptions import (
    KiwiInstallBootImageError
)

log = logging.getLogger('kiwi')


class InstallImageBuilder:
    """
    **Installation image builder**

    :param object xml_state: instance of :class:`XMLState`
    :param str root_dir: system image root directory
    :param str target_dir: target directory path name
    :param object boot_image_task: instance of :class:`BootImage`
    :param dict custom_args: Custom processing arguments defined as hash keys:
        * xz_options: string of XZ compression parameters
    """
    def __init__(
        self, xml_state: XMLState, root_dir: str, target_dir: str,
        boot_image_task: Optional[BootImageBase],
        custom_args: Dict = None
    ) -> None:
        self.arch = Defaults.get_platform_name()
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.xml_state = xml_state
        self.root_filesystem_is_multipath = \
            xml_state.get_oemconfig_oem_multipath_scan()
        self.initrd_system = xml_state.get_initrd_system()
        self.firmware = FirmWare(xml_state)
        self.setup = SystemSetup(
            self.xml_state, self.root_dir
        )
        self.iso_volume_id = self.xml_state.build_type.get_volid() or \
            Defaults.get_install_volume_id()
        self.diskname = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + xml_state.get_image_version(),
                '.raw'
            ]
        )
        self.isoname = ''.join(
            [
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + xml_state.get_image_version(),
                '.install.iso'
            ]
        )
        self.pxename = ''.join(
            [
                xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + xml_state.get_image_version()
            ]
        )
        self.pxetarball = ''.join(
            [
                target_dir, '/', self.pxename, '.install.tar'
            ]
        )
        self.dracut_config_file = ''.join(
            [self.root_dir, Defaults.get_dracut_conf_name()]
        )
        self.squashed_diskname = ''.join(
            [xml_state.xml_data.get_name(), '.raw']
        )
        self.md5name = ''.join(
            [xml_state.xml_data.get_name(), '.md5']
        )
        self.xz_options = custom_args['xz_options'] if custom_args \
            and 'xz_options' in custom_args else None

        self.mbrid = SystemIdentifier()
        self.mbrid.calculate_id()

        self.custom_iso_args: Dict = {}

        if not boot_image_task:
            self.boot_image_task = BootImage.new(
                xml_state, target_dir, root_dir
            )
            self.boot_image_task.prepare()
        else:
            self.boot_image_task = boot_image_task

    def create_install_iso(self) -> None:
        """
        Create an install ISO from the disk_image as hybrid ISO
        bootable via legacy BIOS, EFI and as disk from Stick

        Image types which triggers this builder are:

        * installiso="true|false"
        * installstick="true|false"
        """
        self.media_dir = Temporary(
            prefix='kiwi_install_media.', dir=self.target_dir
        ).new_dir()
        # unpack cdroot user files to media dir
        self.setup.import_cdroot_files(self.media_dir.name)

        # custom iso metadata
        self.custom_iso_args = {
            'meta_data': {
                'volume_id': self.iso_volume_id,
                'mbr_id': self.mbrid.get_id(),
                'efi_mode': self.firmware.efi_mode(),
                'ofw_mode': self.firmware.ofw_mode()
            }
        }

        # the system image transfer is checked against a checksum
        log.info('Creating disk image checksum')
        self.squashed_contents = Temporary(
            prefix='kiwi_install_squashfs.', dir=self.target_dir
        ).new_dir()
        checksum = Checksum(self.diskname)
        checksum.md5(self.squashed_contents.name + '/' + self.md5name)

        # the system image name is stored in a config file
        self._write_install_image_info_to_iso_image()
        if self.initrd_system == 'kiwi':
            self._write_install_image_info_to_boot_image()

        # the system image is stored as squashfs embedded file
        log.info('Creating squashfs embedded disk image')
        Command.run(
            [
                'cp', '-l', self.diskname,
                self.squashed_contents.name + '/' + self.squashed_diskname
            ]
        )
        squashed_image_file = ''.join(
            [
                self.target_dir, '/', self.squashed_diskname, '.squashfs'
            ]
        )
        squashed_image = FileSystemSquashFs(
            device_provider=DeviceProvider(),
            root_dir=self.squashed_contents.name,
            custom_args={
                'compression':
                    self.xml_state.build_type.get_squashfscompression()
            }
        )
        squashed_image.create_on_file(squashed_image_file)
        Command.run(
            ['mv', squashed_image_file, self.media_dir.name]
        )

        log.info(
            'Setting up install image bootloader configuration'
        )
        if self.firmware.efi_mode():
            # setup bootloader config to boot the ISO via EFI
            # This also embedds an MBR and the respective BIOS modules
            # for compat boot. The complete bootloader setup will be
            # based on grub
            bootloader_config = BootLoaderConfig.new(
                'grub2', self.xml_state, root_dir=self.root_dir,
                boot_dir=self.media_dir.name, custom_args={
                    'grub_directory_name':
                        Defaults.get_grub_boot_directory_name(self.root_dir)
                }
            )
            bootloader_config.setup_install_boot_images(
                mbrid=self.mbrid,
                lookup_path=self.boot_image_task.boot_root_directory
            )
        else:
            # setup bootloader config to boot the ISO via isolinux.
            # This allows for booting on x86 platforms in BIOS mode
            # only.
            bootloader_config = BootLoaderConfig.new(
                'isolinux', self.xml_state, root_dir=self.root_dir,
                boot_dir=self.media_dir.name
            )
        IsoToolsBase.setup_media_loader_directory(
            self.boot_image_task.boot_root_directory, self.media_dir.name,
            bootloader_config.get_boot_theme()
        )
        bootloader_config.write_meta_data()
        bootloader_config.setup_install_image_config(
            mbrid=self.mbrid
        )
        bootloader_config.write()

        # create initrd for install image
        log.info('Creating install image boot image')
        self._create_iso_install_kernel_and_initrd()

        # the system image initrd is stored to allow kexec
        self._copy_system_image_initrd_to_iso_image()

        # create iso filesystem from media_dir
        log.info('Creating ISO filesystem')
        iso_image = FileSystemIsoFs(
            device_provider=DeviceProvider(), root_dir=self.media_dir.name,
            custom_args=self.custom_iso_args
        )
        iso_image.create_on_file(self.isoname)
        self.boot_image_task.cleanup()

    def create_install_pxe_archive(self) -> None:
        """
        Create an oem install tar archive suitable for installing a
        disk image via the network using the PXE boot protocol.
        The archive contains:

        * The raw system image xz compressed
        * The raw system image checksum metadata file
        * The append file template for the boot server
        * The system image initrd for kexec
        * The install initrd
        * The kernel

        Image types which triggers this builder are:

        * installpxe="true|false"
        """
        self.pxe_dir = Temporary(
            prefix='kiwi_pxe_install_media.', dir=self.target_dir
        ).new_dir()
        # the system image is transfered as xz compressed variant
        log.info('xz compressing disk image')
        pxe_image_filename = ''.join(
            [
                self.pxe_dir.name, '/',
                self.pxename, '.xz'
            ]
        )
        compress = Compress(
            source_filename=self.diskname,
            keep_source_on_compress=True
        )
        compress.xz(self.xz_options)
        Command.run(
            ['mv', compress.compressed_filename, pxe_image_filename]
        )

        # the system image transfer is checked against a checksum
        log.info('Creating disk image checksum')
        pxe_md5_filename = ''.join(
            [
                self.pxe_dir.name, '/',
                self.pxename, '.md5'
            ]
        )
        checksum = Checksum(self.diskname)
        checksum.md5(pxe_md5_filename)

        # the install image name is stored in a config file
        if self.initrd_system == 'kiwi':
            self._write_install_image_info_to_boot_image()

        # the kexec required system image initrd is stored for dracut kiwi-dump
        if self.initrd_system == 'dracut':
            boot_names = self.boot_image_task.get_boot_names()
            system_image_initrd = os.sep.join(
                [self.root_dir, 'boot', boot_names.initrd_name]
            )
            target_initrd_name = '{0}/{1}.initrd'.format(
                self.pxe_dir.name, self.pxename
            )
            shutil.copy(
                system_image_initrd, target_initrd_name
            )
            os.chmod(target_initrd_name, 420)

        # create pxe config append information
        # this information helps to configure the boot server correctly
        append_filename = ''.join(
            [
                self.pxe_dir.name, '/', self.pxename, '.append'
            ]
        )
        if self.initrd_system == 'kiwi':
            cmdline = 'pxe=1'
        else:
            cmdline = ' '.join(
                [
                    'rd.kiwi.install.pxe',
                    'rd.kiwi.install.image=http://example.com/image.xz'
                ]
            )
        custom_cmdline = self.xml_state.build_type.get_kernelcmdline()
        if custom_cmdline:
            cmdline += ' ' + custom_cmdline
        with open(append_filename, 'w') as append:
            append.write('%s\n' % cmdline)

        # create initrd for pxe install
        log.info('Creating pxe install boot image')
        self._create_pxe_install_kernel_and_initrd()

        # create pxe image bound boot config file, contents can be
        # changed but presence is required.
        log.info('Creating pxe install boot options file')
        configname = '{0}.config.bootoptions'.format(self.pxename)
        shutil.copy(
            os.sep.join([self.root_dir, 'config.bootoptions']),
            os.sep.join([self.pxe_dir.name, configname])
        )

        # create pxe install tarball
        log.info('Creating pxe install archive')
        archive = ArchiveTar(self.pxetarball)

        archive.create(self.pxe_dir.name)
        self.boot_image_task.cleanup()

    def _create_pxe_install_kernel_and_initrd(self) -> None:
        kernelname = 'pxeboot.{0}.kernel'.format(self.pxename)
        initrdname = 'pxeboot.{0}.initrd.xz'.format(self.pxename)
        kernel = Kernel(self.boot_image_task.boot_root_directory)
        if kernel.get_kernel():
            kernel.copy_kernel(self.pxe_dir.name, kernelname)
            os.symlink(
                kernelname, ''.join(
                    [
                        self.pxe_dir.name, '/',
                        self.pxename, '.kernel'
                    ]
                )
            )
        else:
            raise KiwiInstallBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image_task.boot_root_directory
            )
        if self.xml_state.is_xen_server():
            if kernel.get_xen_hypervisor():
                kernel.copy_xen_hypervisor(
                    self.pxe_dir.name,
                    '/pxeboot.{0}.xen.gz'.format(self.pxename)
                )
            else:
                raise KiwiInstallBootImageError(
                    'No hypervisor in boot image tree %s found' %
                    self.boot_image_task.boot_root_directory
                )
        if self.initrd_system == 'dracut':
            self.boot_image_task.include_module('kiwi-dump')
            self.boot_image_task.include_module('kiwi-dump-reboot')
            if self.root_filesystem_is_multipath is False:
                self.boot_image_task.omit_module('multipath')
            for mod in self.xml_state.get_installmedia_initrd_modules('add'):
                self.boot_image_task.include_module(mod)
            for mod in self.xml_state.get_installmedia_initrd_modules('omit'):
                self.boot_image_task.omit_module(mod)
            self.boot_image_task.set_static_modules(
                self.xml_state.get_installmedia_initrd_modules('set')
            )
        self.boot_image_task.create_initrd(
            self.mbrid, 'initrd_kiwi_install',
            install_initrd=True
        )
        Command.run(
            [
                'mv', self.boot_image_task.initrd_filename,
                self.pxe_dir.name + '/{0}'.format(initrdname)
            ]
        )
        os.chmod(self.pxe_dir.name + '/{0}'.format(initrdname), 420)

    def _create_iso_install_kernel_and_initrd(self) -> None:
        boot_path = self.media_dir.name + '/boot/' + self.arch + '/loader'
        Path.create(boot_path)
        kernel = Kernel(self.boot_image_task.boot_root_directory)
        if kernel.get_kernel():
            kernel.copy_kernel(boot_path, '/linux')
        else:
            raise KiwiInstallBootImageError(
                'No kernel in boot image tree %s found' %
                self.boot_image_task.boot_root_directory
            )
        if self.xml_state.is_xen_server():
            if kernel.get_xen_hypervisor():
                kernel.copy_xen_hypervisor(boot_path, '/xen.gz')
            else:
                raise KiwiInstallBootImageError(
                    'No hypervisor in boot image tree %s found' %
                    self.boot_image_task.boot_root_directory
                )
        if self.initrd_system == 'dracut':
            self.boot_image_task.include_module('kiwi-dump')
            self.boot_image_task.include_module('kiwi-dump-reboot')
            if self.root_filesystem_is_multipath is False:
                self.boot_image_task.omit_module('multipath')
            for mod in self.xml_state.get_installmedia_initrd_modules('add'):
                self.boot_image_task.include_module(mod)
            for mod in self.xml_state.get_installmedia_initrd_modules('omit'):
                self.boot_image_task.omit_module(mod)
            self.boot_image_task.set_static_modules(
                self.xml_state.get_installmedia_initrd_modules('set')
            )
            self._add_system_image_boot_options_to_boot_image()
        self.boot_image_task.create_initrd(
            self.mbrid, 'initrd_kiwi_install',
            install_initrd=True
        )
        Command.run(
            [
                'mv', self.boot_image_task.initrd_filename,
                boot_path + '/initrd'
            ]
        )

    def _add_system_image_boot_options_to_boot_image(self) -> None:
        filename = ''.join(
            [self.boot_image_task.boot_root_directory, '/config.bootoptions']
        )
        self.boot_image_task.include_file(os.sep + os.path.basename(filename))

    def _copy_system_image_initrd_to_iso_image(self) -> None:
        boot_names = self.boot_image_task.get_boot_names()
        system_image_initrd = os.sep.join(
            [self.root_dir, 'boot', boot_names.initrd_name]
        )
        shutil.copy(
            system_image_initrd, self.media_dir.name + '/initrd.system_image'
        )

    def _write_install_image_info_to_iso_image(self) -> None:
        iso_trigger = self.media_dir.name + '/config.isoclient'
        with open(iso_trigger, 'w') as iso_system:
            iso_system.write('IMAGE="%s"\n' % self.squashed_diskname)

    def _write_install_image_info_to_boot_image(self) -> None:
        initrd_trigger = \
            self.boot_image_task.boot_root_directory + '/config.vmxsystem'
        with open(initrd_trigger, 'w') as vmx_system:
            vmx_system.write('IMAGE="%s"\n' % self.squashed_diskname)
