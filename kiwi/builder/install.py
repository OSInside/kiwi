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
from tempfile import mkdtemp
import platform
import shutil

# project
from kiwi.command import Command
from kiwi.bootloader.config import BootLoaderConfig
from kiwi.filesystem.squashfs import FileSystemSquashFs
from kiwi.filesystem.isofs import FileSystemIsoFs
from kiwi.firmware import FirmWare
from kiwi.system.identifier import SystemIdentifier
from kiwi.path import Path
from kiwi.defaults import Defaults
from kiwi.utils.checksum import Checksum
from kiwi.logger import log
from kiwi.system.kernel import Kernel
from kiwi.utils.compress import Compress
from kiwi.archive.tar import ArchiveTar
from kiwi.system.setup import SystemSetup

from kiwi.exceptions import (
    KiwiInstallBootImageError
)


class InstallImageBuilder(object):
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
        self, xml_state, root_dir, target_dir, boot_image_task,
        custom_args=None
    ):
        self.arch = platform.machine()
        if self.arch == 'i686' or self.arch == 'i586':
            self.arch = 'ix86'
        self.root_dir = root_dir
        self.target_dir = target_dir
        self.boot_image_task = boot_image_task
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
                target_dir, '/',
                xml_state.xml_data.get_name(),
                '.' + self.arch,
                '-' + xml_state.get_image_version(),
                '.install.tar.xz'
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

        self.media_dir = None
        self.pxe_dir = None
        self.squashed_contents = None
        self.custom_iso_args = None

    def create_install_iso(self):
        """
        Create an install ISO from the disk_image as hybrid ISO
        bootable via legacy BIOS, EFI and as disk from Stick

        Image types which triggers this builder are:

        * installiso="true|false"
        * installstick="true|false"
        """
        self.media_dir = mkdtemp(
            prefix='kiwi_install_media.', dir=self.target_dir
        )
        # unpack cdroot user files to media dir
        self.setup.import_cdroot_files(self.media_dir)

        # custom iso metadata
        self.custom_iso_args = {
            'meta_data': {
                'volume_id': self.iso_volume_id,
                'mbr_id': self.mbrid.get_id(),
                'efi_mode': self.firmware.efi_mode()
            }
        }

        # the system image transfer is checked against a checksum
        log.info('Creating disk image checksum')
        self.squashed_contents = mkdtemp(
            prefix='kiwi_install_squashfs.', dir=self.target_dir
        )
        checksum = Checksum(self.diskname)
        checksum.md5(self.squashed_contents + '/' + self.md5name)

        # the system image name is stored in a config file
        self._write_install_image_info_to_iso_image()
        if self.initrd_system == 'kiwi':
            self._write_install_image_info_to_boot_image()

        # the system image is stored as squashfs embedded file
        log.info('Creating squashfs embedded disk image')
        Command.run(
            [
                'cp', '-l', self.diskname,
                self.squashed_contents + '/' + self.squashed_diskname
            ]
        )
        squashed_image_file = ''.join(
            [
                self.target_dir, '/', self.squashed_diskname, '.squashfs'
            ]
        )
        squashed_image = FileSystemSquashFs(
            device_provider=None, root_dir=self.squashed_contents
        )
        squashed_image.create_on_file(squashed_image_file)
        Command.run(
            ['mv', squashed_image_file, self.media_dir]
        )

        # setup bootloader config to boot the ISO via isolinux
        log.info('Setting up install image bootloader configuration')
        bootloader_config_isolinux = BootLoaderConfig(
            'isolinux', self.xml_state, self.media_dir
        )
        bootloader_config_isolinux.setup_install_boot_images(
            mbrid=None,
            lookup_path=self.boot_image_task.boot_root_directory
        )
        bootloader_config_isolinux.setup_install_image_config(
            mbrid=None
        )
        bootloader_config_isolinux.write()

        # setup bootloader config to boot the ISO via EFI
        bootloader_config_grub = BootLoaderConfig(
            'grub2', self.xml_state, self.media_dir, {
                'grub_directory_name':
                    Defaults.get_grub_boot_directory_name(self.root_dir)
            }
        )
        bootloader_config_grub.setup_install_boot_images(
            mbrid=self.mbrid, lookup_path=self.root_dir
        )
        bootloader_config_grub.setup_install_image_config(
            mbrid=self.mbrid
        )
        bootloader_config_grub.write()

        # create initrd for install image
        log.info('Creating install image boot image')
        self._create_iso_install_kernel_and_initrd()

        # the system image initrd is stored to allow kexec
        self._copy_system_image_initrd_to_iso_image()

        # create iso filesystem from media_dir
        log.info('Creating ISO filesystem')
        iso_image = FileSystemIsoFs(
            device_provider=None, root_dir=self.media_dir,
            custom_args=self.custom_iso_args
        )
        iso_image.create_on_file(self.isoname)

    def create_install_pxe_archive(self):
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
        self.pxe_dir = mkdtemp(
            prefix='kiwi_pxe_install_media.', dir=self.target_dir
        )
        # the system image is transfered as xz compressed variant
        log.info('xz compressing disk image')
        pxe_image_filename = ''.join(
            [
                self.pxe_dir, '/',
                self.xml_state.xml_data.get_name(), '.xz'
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
                self.pxe_dir, '/',
                self.xml_state.xml_data.get_name(), '.md5'
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
                self.pxe_dir, self.xml_state.xml_data.get_name()
            )
            shutil.copy(
                system_image_initrd, target_initrd_name
            )
            os.chmod(target_initrd_name, 420)

        # create pxe config append information
        # this information helps to configure the boot server correctly
        append_filename = ''.join(
            [
                self.pxe_dir, '/',
                self.xml_state.xml_data.get_name(), '.append'
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

        # create pxe install tarball
        log.info('Creating pxe install archive')
        archive = ArchiveTar(
            self.pxename.replace('.xz', '')
        )
        archive.create_xz_compressed(
            self.pxe_dir, xz_options=self.xz_options
        )

    def _create_pxe_install_kernel_and_initrd(self):
        kernel = Kernel(self.boot_image_task.boot_root_directory)
        if kernel.get_kernel():
            kernel.copy_kernel(self.pxe_dir, '/pxeboot.kernel')
            os.symlink(
                'pxeboot.kernel', ''.join(
                    [
                        self.pxe_dir, '/',
                        self.xml_state.xml_data.get_name(), '.kernel'
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
                kernel.copy_xen_hypervisor(self.pxe_dir, '/pxeboot.xen.gz')
            else:
                raise KiwiInstallBootImageError(
                    'No hypervisor in boot image tree %s found' %
                    self.boot_image_task.boot_root_directory
                )
        if self.initrd_system == 'dracut':
            self._create_dracut_install_config()
            self._add_system_image_boot_options_to_boot_image()
        self.boot_image_task.create_initrd(self.mbrid, 'initrd_kiwi_install')
        Command.run(
            [
                'mv', self.boot_image_task.initrd_filename,
                self.pxe_dir + '/pxeboot.initrd.xz'
            ]
        )
        os.chmod(self.pxe_dir + '/pxeboot.initrd.xz', 420)

    def _create_iso_install_kernel_and_initrd(self):
        boot_path = self.media_dir + '/boot/' + self.arch + '/loader'
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
            self._create_dracut_install_config()
            self._add_system_image_boot_options_to_boot_image()
        self.boot_image_task.create_initrd(self.mbrid, 'initrd_kiwi_install')
        Command.run(
            [
                'mv', self.boot_image_task.initrd_filename,
                boot_path + '/initrd'
            ]
        )

    def _add_system_image_boot_options_to_boot_image(self):
        filename = ''.join(
            [self.boot_image_task.boot_root_directory, '/config.bootoptions']
        )
        self.boot_image_task.include_file(
            os.sep + os.path.basename(filename)
        )

    def _copy_system_image_initrd_to_iso_image(self):
        boot_names = self.boot_image_task.get_boot_names()
        system_image_initrd = os.sep.join(
            [self.root_dir, 'boot', boot_names.initrd_name]
        )
        shutil.copy(
            system_image_initrd, self.media_dir + '/initrd.system_image'
        )

    def _write_install_image_info_to_iso_image(self):
        iso_trigger = self.media_dir + '/config.isoclient'
        with open(iso_trigger, 'w') as iso_system:
            iso_system.write('IMAGE="%s"\n' % self.squashed_diskname)

    def _write_install_image_info_to_boot_image(self):
        initrd_trigger = \
            self.boot_image_task.boot_root_directory + '/config.vmxsystem'
        with open(initrd_trigger, 'w') as vmx_system:
            vmx_system.write('IMAGE="%s"\n' % self.squashed_diskname)

    def _create_dracut_install_config(self):
        dracut_config = [
            'hostonly="no"',
            'dracut_rescue_image="no"'
        ]
        dracut_modules = ['kiwi-lib', 'kiwi-dump']
        dracut_modules_omit = ['kiwi-overlay', 'kiwi-live', 'kiwi-repart']
        if self.root_filesystem_is_multipath is False:
            dracut_modules_omit.append('multipath')
        dracut_config.append(
            'add_dracutmodules+=" {0} "'.format(' '.join(dracut_modules))
        )
        dracut_config.append(
            'omit_dracutmodules+=" {0} "'.format(' '.join(dracut_modules_omit))
        )
        with open(self.dracut_config_file, 'w') as config:
            for entry in dracut_config:
                config.write(entry + os.linesep)

    def _delete_dracut_install_config(self):
        if os.path.exists(self.dracut_config_file):
            os.remove(self.dracut_config_file)

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        if self.initrd_system == 'dracut':
            self._delete_dracut_install_config()
        if self.media_dir:
            Path.wipe(self.media_dir)
        if self.pxe_dir:
            Path.wipe(self.pxe_dir)
        if self.squashed_contents:
            Path.wipe(self.squashed_contents)
