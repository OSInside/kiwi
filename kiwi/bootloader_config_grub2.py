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
from logger import log
from bootloader_config_base import BootLoaderConfigBase
from bootloader_template_grub2 import BootLoaderTemplateGrub2
from command import Command
from path import Path
from defaults import Defaults
from firmware import FirmWare

from exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderGrubPlatformError,
    KiwiBootLoaderGrubModulesError,
    KiwiBootLoaderGrubSecureBootError,
    KiwiBootLoaderGrubFontError
)


class BootLoaderConfigGrub2(BootLoaderConfigBase):
    """
        grub2 bootloader configuration.
    """
    def post_init(self):
        arch = platform.machine()
        if arch == 'x86_64':
            self.arch = arch
        else:
            raise KiwiBootLoaderGrubPlatformError(
                'host architecture %s not supported for grub2 setup' % arch
            )

        self.terminal = 'gfxterm'
        self.bootpath = self.get_boot_path()
        self.gfxmode = self.__get_gfxmode()
        self.theme = self.get_boot_theme()
        self.timeout = self.get_boot_timeout_seconds()
        self.cmdline = self.get_boot_cmdline()
        self.cmdline_failsafe = self.get_failsafe_boot_cmdline()
        self.failsafe_boot = self.failsafe_boot_entry_requested()
        self.hypervisor_domain = self.get_hypervisor_domain()
        self.firmware = FirmWare(
            self.xml_state.build_type.get_firmware()
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

        self.grub2 = BootLoaderTemplateGrub2()
        self.config = None
        self.efi_boot_path = None

    def write(self):
        """
            Write grub.cfg file to all required places
        """
        log.info('Writing grub.cfg file')
        config_dir = self.__get_grub_boot_path()
        config_file = config_dir + '/grub.cfg'
        if self.config:
            Path.create(config_dir)
            with open(config_file, 'w') as config:
                config.write(self.config)

            if self.efi_boot_path:
                config_file = self.efi_boot_path + '/grub.cfg'
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
        parameters = {
            'search_params': '--fs-uuid --set=root ' + uuid,
            'default_boot': '0',
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': self.cmdline,
            'failsafe_boot_options': self.cmdline_failsafe,
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
            log.info('--> Using EFI/BIOS hybrid boot disk template')
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
            Create the grub.cfg in memory from a template suitable to boot
            from an ISO image in EFI boot mode
        """
        log.info('Creating grub install config file from template')
        parameters = {
            'search_params': '--file --set=root /boot/' + mbrid.get_id(),
            'default_boot': '0',
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': self.cmdline,
            'failsafe_boot_options': self.cmdline_failsafe,
            'gfxmode': self.gfxmode,
            'theme': self.theme,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_install_title(),
            'bootpath': '/boot/x86_64/loader',
        }
        if self.multiboot:
            log.info('--> Using EFI multiboot install template')
            parameters['hypervisor'] = hypervisor
            template = self.grub2.get_multiboot_install_template(
                self.failsafe_boot, self.terminal
            )
        else:
            log.info('--> Using EFI boot install template')
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
            Create the grub.cfg in memory from a template suitable to boot
            a live system from an ISO image in EFI boot mode
        """
        log.info('Creating grub live ISO config file from template')
        parameters = {
            'search_params': '--file --set=root /boot/' + mbrid.get_id(),
            'default_boot': '0',
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': self.cmdline,
            'failsafe_boot_options': self.cmdline_failsafe,
            'gfxmode': self.gfxmode,
            'theme': self.theme,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_title(plain=True),
            'bootpath': '/boot/x86_64/loader',
        }
        if self.multiboot:
            log.info('--> Using EFI multiboot template')
            parameters['hypervisor'] = hypervisor
            template = self.grub2.get_multiboot_iso_template(
                self.failsafe_boot, self.terminal
            )
        else:
            log.info('--> Using EFI boot template')
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
            Using grub2 to boot an install media means to support EFI
            boot of the install media. Therefore an EFI image needs to
            be build or used and transfered into an embedded vfat image.
            The non EFI boot of the install media is handled in the
            isolinux boot loader configuration
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

        if self.firmware.efi_mode() == 'uefi':
            log.info('--> Using signed secure boot efi image')
            self.__setup_secure_boot_efi_image(lookup_path)
        else:
            log.info('--> Creating unsigned efi image')
            self.__copy_efi_modules_to_boot_directory(lookup_path)
            self.__create_efi_image(mbrid=mbrid)

        self.__create_embedded_fat_efi_image()

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        # same action as for install media
        self.setup_install_boot_images(mbrid, lookup_path)

    def setup_disk_boot_images(self, boot_uuid, lookup_path=None):
        """
            EFI and bios images needs to be build or used if provided
            by the distribution
        """
        log.info('Creating grub bootloader images')

        if self.firmware.efi_mode():
            self.efi_boot_path = self.create_efi_path()

        self.__copy_theme_data_to_boot_directory(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            log.info('--> Creating unsigned efi image')
            self.__copy_efi_modules_to_boot_directory(lookup_path)
            self.__create_efi_image(uuid=boot_uuid)
        elif self.firmware.efi_mode() == 'uefi':
            log.info('--> Using signed secure boot efi image')
            self.__setup_secure_boot_efi_image(lookup_path)

        log.info('--> Creating bios core image')
        self.__copy_bios_modules_to_boot_directory(lookup_path)
        self.__create_bios_boot_image(boot_uuid)

    def __setup_secure_boot_efi_image(self, lookup_path):
        """
            use prebuilt and signed efi images provided by the distribution
        """
        secure_efi_lookup_path = self.root_dir + '/usr/lib64/efi/'
        if lookup_path:
            secure_efi_lookup_path = lookup_path
        shim_image = secure_efi_lookup_path + Defaults.get_shim_name()
        if not os.path.exists(shim_image):
            raise KiwiBootLoaderGrubSecureBootError(
                'Microsoft signed shim loader %s not found' % shim_image
            )
        grub_image = secure_efi_lookup_path + Defaults.get_signed_grub_name()
        if not os.path.exists(grub_image):
            raise KiwiBootLoaderGrubSecureBootError(
                'Signed grub2 efi loader %s not found' % grub_image
            )
        Command.run(
            ['cp', shim_image, self.__get_efi_image_name()]
        )
        Command.run(
            ['cp', grub_image, self.efi_boot_path]
        )

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

    def __create_efi_image(self, uuid=None, mbrid=None):
        """
            create efi image
        """
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
                'grub2-mkimage', '-O', self.__get_efi_format(),
                '-o', self.__get_efi_image_name(),
                '-c', early_boot_script,
                '-p', self.get_boot_path() + '/grub2', '-d',
                self.__get_grub_boot_path() + '/' + self.__get_efi_format()
            ] + self.__get_efi_modules()
        )

    def __create_bios_boot_image(self, uuid):
        """
            create bios image
        """
        early_boot_script = self.__get_grub_boot_path() + '/earlyboot.cfg'
        self.__create_early_boot_script_for_uuid_search(
            early_boot_script, uuid
        )
        Command.run(
            [
                'grub2-mkimage', '-O', self.__get_bios_format(),
                '-o', self.__get_bios_image_name(),
                '-c', early_boot_script,
                '-p', self.get_boot_path() + '/grub2', '-d',
                self.__get_grub_boot_path() + '/' + self.__get_bios_format()
            ] + self.__get_bios_modules()
        )

    def __create_early_boot_script_for_uuid_search(self, filename, uuid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'search --fs-uuid --set=root %s\n' % uuid
            )
            early_boot.write(
                'set prefix=($root)%s/grub2\n' % self.get_boot_path()
            )

    def __create_early_boot_script_for_mbrid_search(self, filename, mbrid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'search --file --set=root /boot/%s\n' % mbrid.get_id()
            )
            early_boot.write(
                'set prefix=($root)/boot/grub2\n'
            )

    def __get_grub_boot_path(self):
        return self.root_dir + '/boot/grub2'

    def __get_basic_modules(self):
        return [
            'ext2',
            'iso9660',
            'linux',
            'echo',
            'configfile',
            'search_label',
            'search_fs_file',
            'search',
            'search_fs_uuid',
            'ls',
            'normal',
            'gzio',
            'png',
            'fat',
            'gettext',
            'font',
            'minicmd',
            'gfxterm',
            'gfxmenu',
            'video',
            'video_fb',
            'xfs',
            'btrfs',
            'lvm',
            'multiboot'
        ]

    def __get_efi_modules(self):
        modules = self.__get_basic_modules() + [
            'part_gpt',
            'efi_gop',
            'efi_uga',
            'linuxefi'
        ]
        return modules

    def __get_bios_modules(self):
        modules = self.__get_basic_modules() + [
            'part_gpt',
            'part_msdos',
            'biosdisk',
            'vga',
            'vbe',
            'chain',
            'boot'
        ]
        return modules

    def __get_efi_image_name(self):
        efi_image_name = None
        if self.arch == 'x86_64':
            efi_image_name = 'bootx64.efi'
        if efi_image_name:
            return ''.join(
                [self.efi_boot_path, '/', efi_image_name]
            )

    def __get_bios_image_name(self):
        return ''.join(
            [
                self.__get_grub_boot_path(), '/',
                self.__get_bios_format(), '/core.img'
            ]
        )

    def __get_efi_format(self):
        if self.arch == 'x86_64':
            return 'x86_64-efi'

    def __get_bios_format(self):
        if self.firmware.ec2_mode():
            return 'x86_64-xen'
        else:
            return 'i386-pc'

    def __get_efi_modules_path(self, lookup_path=None):
        if not lookup_path:
            lookup_path = self.root_dir
        module_dir = ''.join(
            [
                lookup_path, '/usr/lib/grub2/',
                self.__get_efi_format()
            ]
        )
        return module_dir

    def __get_bios_modules_path(self, lookup_path=None):
        if not lookup_path:
            lookup_path = self.root_dir
        module_dir = ''.join(
            [
                lookup_path, '/usr/lib/grub2/',
                self.__get_bios_format()
            ]
        )
        return module_dir

    def __get_gfxmode(self):
        selected_gfxmode = 'keep'
        gfxmode = {
            '0x301': '640x480',
            '0x310': '640x480',
            '0x311': '640x480',
            '0x312': '640x480',
            '0x303': '800x600',
            '0x313': '800x600',
            '0x314': '800x600',
            '0x315': '800x600',
            '0x305': '1024x768',
            '0x316': '1024x768',
            '0x317': '1024x768',
            '0x318': '1024x768',
            '0x307': '1280x1024',
            '0x319': '1280x1024',
            '0x31a': '1280x1024',
            '0x31b': '1280x1024',
        }
        requested_gfxmode = self.xml_state.build_type.get_vga()
        if requested_gfxmode in gfxmode:
            selected_gfxmode = gfxmode[requested_gfxmode]
        return selected_gfxmode

    def __copy_theme_data_to_boot_directory(self, lookup_path):
        if not lookup_path:
            lookup_path = self.root_dir
        boot_unicode_font = self.root_dir + '/boot/unicode.pf2'
        if not os.path.exists(boot_unicode_font):
            unicode_font = lookup_path + '/usr/share/grub2/unicode.pf2'
            try:
                Command.run(
                    ['cp', unicode_font, boot_unicode_font]
                )
            except Exception:
                raise KiwiBootLoaderGrubFontError(
                    'Unicode font %s not found' % unicode_font
                )

        boot_theme_dir = self.root_dir + '/boot/grub2/themes'
        if self.theme and not os.path.exists(boot_theme_dir):
            Path.create(boot_theme_dir)
            theme_dir = \
                lookup_path + '/usr/share/grub2/themes/' + self.theme
            if os.path.exists(theme_dir):
                Command.run(
                    ['rsync', '-zav', theme_dir, boot_theme_dir],
                )
            else:
                log.warning('Theme %s not found', theme_dir)

    def __copy_efi_modules_to_boot_directory(self, lookup_path):
        self.__copy_modules_to_boot_directory_from(
            self.__get_efi_modules_path(lookup_path)
        )

    def __copy_bios_modules_to_boot_directory(self, lookup_path):
        self.__copy_modules_to_boot_directory_from(
            self.__get_bios_modules_path(lookup_path)
        )

    def __copy_modules_to_boot_directory_from(self, module_path):
        boot_module_path = \
            self.__get_grub_boot_path() + '/' + os.path.basename(module_path)
        if not os.path.exists(boot_module_path):
            try:
                Command.run(
                    ['cp', '-a', module_path, boot_module_path]
                )
            except Exception:
                raise KiwiBootLoaderGrubModulesError(
                    'grub2 modules %s not found' % module_path
                )
