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
from .base import BootLoaderConfigBase
from ..template.grub2 import BootLoaderTemplateGrub2
from ...command import Command
from ...defaults import Defaults
from ...firmware import FirmWare
from ...logger import log
from ...path import Path
from ...utils.sync import DataSync

from ...exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderGrubPlatformError,
    KiwiBootLoaderGrubModulesError,
    KiwiBootLoaderGrubFontError,
    KiwiBootLoaderGrubDataError
)


class BootLoaderConfigGrub2(BootLoaderConfigBase):
    """
        grub2 bootloader configuration.
    """
    def post_init(self, custom_args):
        self.custom_args = custom_args
        arch = platform.machine()
        if arch == 'x86_64':
            # grub2 support for bios and efi systems
            self.arch = arch
        elif arch.startswith('ppc64'):
            # grub2 support for ofw and opal systems
            self.arch = arch
        elif arch == 'i686' or arch == 'i586':
            # grub2 support for bios systems
            self.arch = 'ix86'
        elif arch == 'aarch64' or arch.startswith('arm'):
            # grub2 support for efi systems
            self.arch = arch
        else:
            raise KiwiBootLoaderGrubPlatformError(
                'host architecture %s not supported for grub2 setup' % arch
            )

        self.terminal = 'gfxterm'
        self.gfxmode = self.get_gfxmode('grub2')
        self.bootpath = self.get_boot_path()
        self.theme = self.get_boot_theme()
        self.timeout = self.get_boot_timeout_seconds()
        self.failsafe_boot = self.failsafe_boot_entry_requested()
        self.hypervisor_domain = self.get_hypervisor_domain()
        self.firmware = FirmWare(
            self.xml_state
        )
        self.hybrid_boot = True
        self.multiboot = False
        if self.hypervisor_domain:
            if self.hypervisor_domain == 'dom0':
                self.hybrid_boot = False
                self.multiboot = True
            elif self.hypervisor_domain == 'domU':
                self.hybrid_boot = False
                self.multiboot = False

        self.xen_guest = False
        if self.hypervisor_domain == 'domU' or self.firmware.ec2_mode():
            self.xen_guest = True

        self.grub2 = BootLoaderTemplateGrub2()
        self.config = None
        self.efi_boot_path = None
        self.boot_directory_name = 'grub2'

    def write(self):
        log.info('Writing grub.cfg file')
        config_dir = self.__get_grub_boot_path()
        config_file = config_dir + '/grub.cfg'
        if self.config:
            Path.create(config_dir)
            with open(config_file, 'w') as config:
                config.write(self.config)

    def setup_disk_image_config(
        self, uuid, hypervisor='xen.gz', kernel='linux.vmx', initrd='initrd.vmx'
    ):
        """
            Create the grub.cfg in memory from a template suitable to boot
            from a disk image
        """
        log.info('Creating grub config file from template')
        cmdline = self.get_boot_cmdline(uuid)
        cmdline_failsafe = ' '.join(
            [cmdline, self.get_failsafe_kernel_options()]
        )
        parameters = {
            'search_params': '--fs-uuid --set=root ' + uuid,
            'default_boot': '0',
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': cmdline,
            'failsafe_boot_options': cmdline_failsafe,
            'gfxmode': self.gfxmode,
            'theme': self.theme,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_title(),
            'bootpath': self.bootpath,
        }
        if self.multiboot:
            log.info('--> Using multiboot disk template')
            parameters['hypervisor'] = hypervisor
            template = self.grub2.get_multiboot_disk_template(
                self.failsafe_boot, self.terminal
            )
        else:
            log.info('--> Using hybrid boot disk template')
            template = self.grub2.get_disk_template(
                self.failsafe_boot, self.hybrid_boot, self.terminal
            )
        try:
            self.config = template.substitute(parameters)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def setup_install_image_config(
        self, mbrid, hypervisor='xen.gz', kernel='linux', initrd='initrd'
    ):
        """
            Create grub config file to boot from an ISO install image
        """
        log.info('Creating grub install config file from template')
        cmdline = self.get_boot_cmdline()
        cmdline_failsafe = ' '.join(
            [cmdline, self.get_failsafe_kernel_options()]
        )
        parameters = {
            'search_params': '--file --set=root /boot/' + mbrid.get_id(),
            'default_boot': '0',
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': cmdline,
            'failsafe_boot_options': cmdline_failsafe,
            'gfxmode': self.gfxmode,
            'theme': self.theme,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_install_title(),
            'bootpath': '/boot/' + self.arch + '/loader',
        }
        if self.multiboot:
            log.info('--> Using multiboot install template')
            parameters['hypervisor'] = hypervisor
            template = self.grub2.get_multiboot_install_template(
                self.failsafe_boot, self.terminal
            )
        else:
            log.info('--> Using standard boot install template')
            hybrid_boot = True
            template = self.grub2.get_install_template(
                self.failsafe_boot, hybrid_boot, self.terminal
            )
        try:
            self.config = template.substitute(parameters)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def setup_live_image_config(
        self, mbrid, hypervisor='xen.gz', kernel='linux', initrd='initrd'
    ):
        """
            Create grub config file to boot a live media ISO image
        """
        log.info('Creating grub live ISO config file from template')
        cmdline = self.get_boot_cmdline()
        cmdline_failsafe = ' '.join(
            [cmdline, self.get_failsafe_kernel_options()]
        )
        parameters = {
            'search_params': '--file --set=root /boot/' + mbrid.get_id(),
            'default_boot': '0',
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': cmdline,
            'failsafe_boot_options': cmdline_failsafe,
            'gfxmode': self.gfxmode,
            'theme': self.theme,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_title(plain=True),
            'bootpath': '/boot/' + self.arch + '/loader',
        }
        if self.multiboot:
            log.info('--> Using multiboot template')
            parameters['hypervisor'] = hypervisor
            template = self.grub2.get_multiboot_iso_template(
                self.failsafe_boot, self.terminal
            )
        else:
            log.info('--> Using standard boot template')
            hybrid_boot = True
            template = self.grub2.get_iso_template(
                self.failsafe_boot, hybrid_boot, self.terminal
            )
        try:
            self.config = template.substitute(parameters)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def setup_install_boot_images(self, mbrid, lookup_path=None):
        """
            In order to boot from the ISO grub modules, images
            and theme data needs to be created and provided at
            the correct place on the iso filesystem
        """
        log.info('Creating grub bootloader images')
        self.efi_boot_path = self.create_efi_path(in_sub_dir='')

        log.info('--> Creating identifier file %s', mbrid.get_id())
        Path.create(
            self.__get_grub_boot_path()
        )
        mbrid.write(
            self.root_dir + '/boot/' + mbrid.get_id()
        )
        mbrid.write(
            self.root_dir + '/boot/mbrid'
        )

        self.__copy_theme_data_to_boot_directory(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            log.info('--> Creating unsigned efi image')
            self.__create_efi_image(mbrid=mbrid, lookup_path=lookup_path)
            self.__copy_efi_modules_to_boot_directory(lookup_path)
        else:
            log.info(
                '--> Using signed secure boot efi image, done by shim-install'
            )

        self.__create_embedded_fat_efi_image()

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        # same action as for install media
        self.setup_install_boot_images(mbrid, lookup_path)

    def setup_disk_boot_images(self, boot_uuid, lookup_path=None):
        """
            In order to boot from the disk grub modules, images
            and theme data needs to be created and provided at
            the correct place in the filesystem
        """
        log.info('Creating grub bootloader images')

        if self.firmware.efi_mode():
            self.efi_boot_path = self.create_efi_path()

        self.__copy_theme_data_to_boot_directory(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            log.info('--> Creating unsigned efi image')
            self.__create_efi_image(uuid=boot_uuid, lookup_path=lookup_path)
            self.__copy_efi_modules_to_boot_directory(lookup_path)
        elif self.firmware.efi_mode() == 'uefi':
            log.info(
                '--> Using signed secure boot efi image, done by shim-install'
            )

        if self.xen_guest:
            self.__copy_xen_modules_to_boot_directory(lookup_path)

    def __create_embedded_fat_efi_image(self):
        Path.create(self.root_dir + '/boot/' + self.arch)
        efi_fat_image = ''.join(
            [self.root_dir + '/boot/', self.arch, '/efi']
        )
        Command.run(
            ['qemu-img', 'create', efi_fat_image, '4M']
        )
        Command.run(
            ['mkdosfs', '-n', 'BOOT', efi_fat_image]
        )
        Command.run(
            [
                'mcopy', '-Do', '-s', '-i', efi_fat_image,
                self.root_dir + '/EFI', '::'
            ]
        )

    def __create_efi_image(self, uuid=None, mbrid=None, lookup_path=None):
        early_boot_script = self.efi_boot_path + '/earlyboot.cfg'
        if uuid:
            self.__create_early_boot_script_for_uuid_search(
                early_boot_script, uuid
            )
        else:
            self.__create_early_boot_script_for_mbrid_search(
                early_boot_script, mbrid
            )
        Command.run(
            [
                'grub2-mkimage',
                '-O', Defaults.get_efi_module_directory_name(self.arch),
                '-o', self.__get_efi_image_name(),
                '-c', early_boot_script,
                '-p', self.get_boot_path() + '/' + self.boot_directory_name,
                '-d', self.__get_efi_modules_path(lookup_path)
            ] + Defaults.get_grub_efi_modules()
        )

    def __create_early_boot_script_for_uuid_search(self, filename, uuid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'search --fs-uuid --set=root %s\n' % uuid
            )
            early_boot.write(
                'set prefix=($root)%s/%s\n' % (
                    self.get_boot_path(), self.boot_directory_name
                )
            )

    def __create_early_boot_script_for_mbrid_search(self, filename, mbrid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'search --file --set=root /boot/%s\n' % mbrid.get_id()
            )
            early_boot.write(
                'set prefix=($root)/boot/%s\n' % self.boot_directory_name
            )

    def __get_grub_boot_path(self):
        return self.root_dir + '/boot/' + self.boot_directory_name

    def __get_efi_image_name(self):
        return self.efi_boot_path + '/' + Defaults.get_efi_image_name(self.arch)

    def __get_efi_modules_path(self, lookup_path=None):
        return self.__get_module_path(
            Defaults.get_efi_module_directory_name(self.arch),
            lookup_path
        )

    def __get_xen_modules_path(self, lookup_path=None):
        return self.__get_module_path(
            Defaults.get_efi_module_directory_name('x86_64_xen'),
            lookup_path
        )

    def __get_module_path(self, format_name, lookup_path=None):
        if not lookup_path:
            lookup_path = self.root_dir
        return ''.join(
            [
                self.__find_grub_data(lookup_path + '/usr/lib'),
                '/', format_name
            ]
        )

    def __copy_theme_data_to_boot_directory(self, lookup_path):
        if not lookup_path:
            lookup_path = self.root_dir
        boot_unicode_font = self.root_dir + '/boot/unicode.pf2'
        if not os.path.exists(boot_unicode_font):
            unicode_font = self.__find_grub_data(lookup_path + '/usr/share') + \
                '/unicode.pf2'
            try:
                Command.run(
                    ['cp', unicode_font, boot_unicode_font]
                )
            except Exception:
                raise KiwiBootLoaderGrubFontError(
                    'Unicode font %s not found' % unicode_font
                )

        boot_theme_dir = self.root_dir + '/boot/' + \
            self.boot_directory_name + '/themes'
        if self.theme and not os.path.exists(boot_theme_dir):
            Path.create(boot_theme_dir)
            theme_dir = self.__find_grub_data(lookup_path + '/usr/share') + \
                '/themes/' + self.theme
            if os.path.exists(theme_dir):
                data = DataSync(
                    theme_dir, boot_theme_dir
                )
                data.sync_data(
                    options=['-z', '-a']
                )
            else:
                log.warning('Theme %s not found', theme_dir)

    def __copy_efi_modules_to_boot_directory(self, lookup_path):
        self.__copy_modules_to_boot_directory_from(
            self.__get_efi_modules_path(lookup_path)
        )

    def __copy_xen_modules_to_boot_directory(self, lookup_path):
        self.__copy_modules_to_boot_directory_from(
            self.__get_xen_modules_path(lookup_path)
        )

    def __copy_modules_to_boot_directory_from(self, module_path):
        boot_module_path = \
            self.__get_grub_boot_path() + '/' + os.path.basename(module_path)
        try:
            data = DataSync(
                module_path + '/', boot_module_path
            )
            data.sync_data(
                options=['-z', '-a']
            )
        except Exception as e:
            raise KiwiBootLoaderGrubModulesError(
                'Module synchronisation failed with: %s' % format(e)
            )

    def __find_grub_data(self, lookup_path):
        """
            depending on the distribution grub could be installed below
            a grub2 or grub directory. Therefore this information needs
            to be dynamically looked up
        """
        for grub_name in ['grub2', 'grub']:
            grub_path = lookup_path + '/' + grub_name
            if os.path.exists(grub_path):
                return grub_path

        raise KiwiBootLoaderGrubDataError(
            'No grub2 installation found in %s' % lookup_path
        )
