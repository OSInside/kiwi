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
import shutil

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
    KiwiBootLoaderGrubSecureBootError,
    KiwiBootLoaderGrubFontError,
    KiwiBootLoaderGrubDataError
)


class BootLoaderConfigGrub2(BootLoaderConfigBase):
    """
    grub2 bootloader configuration.

    Attributes

    * :attr:`terminal`
        terminal mode set to gfxterm

    * :attr:`gfxmode`
        configured or default graphics mode

    * :attr:`bootpath`
        boot path according to configuration

    * :attr:`theme`
        configured bootloader theme or none

    * :attr:`timeout`
        configured or default boot timeout

    * :attr:`failsafe_boot`
        failsafe mode requested true|false

    * :attr:`hypervisor_domain`
        configured hypervisor domain name or none

    * :attr:`firmware`
        Instance of FirmWare

    * :attr:`hybrid_boot`
        hybrid boot requested true|false

    * :attr:`multiboot`
        multiboot requested true|false

    * :attr:`xen_guest`
        Xen guest setup true|false

    * :attr:`grub2`
        Instance of config template: BootLoaderTemplateGrub2

    * :attr:`config`
        Configuration data from template substitution

    * :attr:`efi_boot_path`
        EFI boot path according to configuration

    * :attr:`boot_directory_name`
        grub boot directory below boot path set to: grub2
    """
    def post_init(self, custom_args):
        """
        grub2 post initialization method

        Setup class attributes
        """
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

        self.terminal = self.xml_state.build_type.get_bootloader_console() \
            or 'gfxterm'
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
        """
        Write grub.cfg file
        """
        log.info('Writing grub.cfg file')
        config_dir = self._get_grub_boot_path()
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

        :param string uuid: boot device UUID
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
        """
        log.info('Creating grub config file from template')
        cmdline = self.get_boot_cmdline(uuid)
        cmdline_failsafe = ' '.join(
            [cmdline, Defaults.get_failsafe_kernel_options()]
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

        :param string mbrid: mbrid file name on boot device
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
        """
        log.info('Creating grub install config file from template')
        cmdline = self.get_boot_cmdline()
        cmdline_failsafe = ' '.join(
            [cmdline, Defaults.get_failsafe_kernel_options()]
        )
        parameters = {
            'search_params': '--file --set=root /boot/' + mbrid.get_id(),
            'default_boot': self.get_install_image_boot_default(),
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

        :param string mbrid: mbrid file name on boot device
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
        """
        log.info('Creating grub live ISO config file from template')
        cmdline = self.get_boot_cmdline()
        cmdline_failsafe = ' '.join(
            [cmdline, Defaults.get_failsafe_kernel_options()]
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
        Create/Provide grub boot images and metadata

        In order to boot from the ISO grub modules, images and theme
        data needs to be created and provided at the correct place on
        the iso filesystem

        :param string mbrid: mbrid file name on boot device
        :param string lookup_path: custom module lookup path
        """
        log.info('Creating grub bootloader images')
        self.efi_boot_path = self.create_efi_path(in_sub_dir='')

        log.info('--> Creating identifier file %s', mbrid.get_id())
        Path.create(
            self._get_grub_boot_path()
        )
        mbrid.write(
            self.root_dir + '/boot/' + mbrid.get_id()
        )
        mbrid.write(
            self.root_dir + '/boot/mbrid'
        )

        self._copy_theme_data_to_boot_directory(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            log.info('--> Creating unsigned efi image')
            self._create_efi_image(mbrid=mbrid, lookup_path=lookup_path)
            self._copy_efi_modules_to_boot_directory(lookup_path)
        elif self.firmware.efi_mode() == 'uefi':
            log.info('--> Setting up shim secure boot efi image')
            self._copy_efi_modules_to_boot_directory(lookup_path)
            self._setup_secure_boot_efi_image(lookup_path)

        self._create_embedded_fat_efi_image()

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        """
        Create/Provide grub boot images and metadata

        Calls setup_install_boot_images because no different action required
        """
        self.setup_install_boot_images(mbrid, lookup_path)

    def setup_disk_boot_images(self, boot_uuid, lookup_path=None):
        """
        Create/Provide grub boot images and metadata

        In order to boot from the disk grub modules, images and theme
        data needs to be created and provided at the correct place in
        the filesystem

        :param string boot_uuid: boot device UUID
        :param string lookup_path: custom module lookup path
        """
        log.info('Creating grub bootloader images')

        if self.firmware.efi_mode():
            self.efi_boot_path = self.create_efi_path()

        self._copy_theme_data_to_boot_directory(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            log.info('--> Creating unsigned efi image')
            self._create_efi_image(uuid=boot_uuid, lookup_path=lookup_path)
            self._copy_efi_modules_to_boot_directory(lookup_path)
        elif self.firmware.efi_mode() == 'uefi':
            self._copy_efi_modules_to_boot_directory(lookup_path)
            log.info(
                '--> Using signed secure boot efi image, done by shim-install'
            )

        if self.xen_guest:
            self._copy_xen_modules_to_boot_directory(lookup_path)

    def _setup_secure_boot_efi_image(self, lookup_path):
        """
        Provide the shim loader and the shim signed grub loader
        in the required boot path. Normally this task is done by
        the shim-install tool. However, shim-install does not exist
        on all distributions and the script does not operate well
        in e.g CD environments from which we generate live and/or
        install media. Thus shim-install is used if possible at
        install time of the bootloader because it requires access
        to the target block device. In any other case this setup
        code should act as the fallback solution
        """
        secure_efi_lookup_path = self.root_dir + '/usr/lib64/efi/'
        if lookup_path:
            secure_efi_lookup_path = lookup_path + '/usr/lib64/efi/'
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
            ['cp', shim_image, self._get_efi_image_name()]
        )
        Command.run(
            ['cp', grub_image, self.efi_boot_path]
        )

    def _create_embedded_fat_efi_image(self):
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

    def _create_efi_image(self, uuid=None, mbrid=None, lookup_path=None):
        early_boot_script = self.efi_boot_path + '/earlyboot.cfg'
        if uuid:
            self._create_early_boot_script_for_uuid_search(
                early_boot_script, uuid
            )
        else:
            self._create_early_boot_script_for_mbrid_search(
                early_boot_script, mbrid
            )
        Command.run(
            [
                'grub2-mkimage',
                '-O', Defaults.get_efi_module_directory_name(self.arch),
                '-o', self._get_efi_image_name(),
                '-c', early_boot_script,
                '-p', self.get_boot_path() + '/' + self.boot_directory_name,
                '-d', self._get_efi_modules_path(lookup_path)
            ] + Defaults.get_grub_efi_modules(multiboot=self.xen_guest)
        )

    def _create_early_boot_script_for_uuid_search(self, filename, uuid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'search --fs-uuid --set=root %s\n' % uuid
            )
            early_boot.write(
                'set prefix=($root)%s/%s\n' % (
                    self.get_boot_path(), self.boot_directory_name
                )
            )

    def _create_early_boot_script_for_mbrid_search(self, filename, mbrid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'search --file --set=root /boot/%s\n' % mbrid.get_id()
            )
            early_boot.write(
                'set prefix=($root)/boot/%s\n' % self.boot_directory_name
            )

    def _get_grub_boot_path(self):
        return self.root_dir + '/boot/' + self.boot_directory_name

    def _get_efi_image_name(self):
        return self.efi_boot_path + '/' + Defaults.get_efi_image_name(self.arch)

    def _get_efi_modules_path(self, lookup_path=None):
        return self._get_module_path(
            Defaults.get_efi_module_directory_name(self.arch),
            lookup_path
        )

    def _get_xen_modules_path(self, lookup_path=None):
        return self._get_module_path(
            Defaults.get_efi_module_directory_name('x86_64_xen'),
            lookup_path
        )

    def _get_module_path(self, format_name, lookup_path=None):
        if not lookup_path:
            lookup_path = self.root_dir
        return ''.join(
            [
                self._find_grub_data(lookup_path + '/usr/lib'),
                '/', format_name
            ]
        )

    def _fixup_legacy_grub_location(self):
        legacy_grub_theme_dir = self.root_dir + '/boot/grub/themes'
        legacy_font = self.root_dir + '/boot/grub/unicode.pf2'
        grub_dir = '/'.join(
            [self.root_dir, 'boot', self.boot_directory_name]
        )
        if os.path.exists(legacy_grub_theme_dir):
            # found grub2 theme directory in legacy grub directory
            Path.wipe(grub_dir + '/themes')
            shutil.copytree(legacy_grub_theme_dir, grub_dir + '/themes')
        if os.path.exists(legacy_font):
            # found grub2 unicode font in legacy grub directory
            shutil.copy(legacy_font, grub_dir)

    def _copy_theme_data_to_boot_directory(self, lookup_path):
        self._fixup_legacy_grub_location()
        if not lookup_path:
            lookup_path = self.root_dir
        boot_unicode_font = self.root_dir + '/boot/unicode.pf2'
        if not os.path.exists(boot_unicode_font):
            unicode_font = self._find_grub_data(lookup_path + '/usr/share') + \
                '/unicode.pf2'
            try:
                Command.run(
                    ['cp', unicode_font, boot_unicode_font]
                )
            except Exception:
                raise KiwiBootLoaderGrubFontError(
                    'Unicode font %s not found' % unicode_font
                )

        boot_theme_dir = os.sep.join(
            [self.root_dir, 'boot', self.boot_directory_name, 'themes']
        )
        if self.theme and not os.path.exists(boot_theme_dir):
            Path.create(boot_theme_dir)
            theme_dir = self._find_grub_data(lookup_path + '/usr/share') + \
                '/themes/' + self.theme
            if os.path.exists(theme_dir):
                data = DataSync(
                    theme_dir, boot_theme_dir
                )
                data.sync_data(
                    options=['-z', '-a']
                )

        self._check_boot_theme_exists()

    def _check_boot_theme_exists(self):
        if self.theme:
            theme_dir = os.sep.join(
                [
                    self.root_dir, 'boot', self.boot_directory_name,
                    'themes', self.theme
                ]
            )
            if not os.path.exists(theme_dir):
                log.warning('Theme %s not found', theme_dir)
                log.warning('Set bootloader terminal to console mode')
                self.terminal = 'console'

    def _copy_efi_modules_to_boot_directory(self, lookup_path):
        self._copy_modules_to_boot_directory_from(
            self._get_efi_modules_path(lookup_path)
        )

    def _copy_xen_modules_to_boot_directory(self, lookup_path):
        self._copy_modules_to_boot_directory_from(
            self._get_xen_modules_path(lookup_path)
        )

    def _copy_modules_to_boot_directory_from(self, module_path):
        boot_module_path = \
            self._get_grub_boot_path() + '/' + os.path.basename(module_path)
        try:
            data = DataSync(
                module_path + '/', boot_module_path
            )
            data.sync_data(
                options=['-z', '-a'], exclude=['*.module']
            )
        except Exception as e:
            raise KiwiBootLoaderGrubModulesError(
                'Module synchronisation failed with: %s' % format(e)
            )

    def _find_grub_data(self, lookup_path):
        grub_path = Defaults.get_grub_path(lookup_path)
        if grub_path:
            return grub_path

        raise KiwiBootLoaderGrubDataError(
            'No grub2 installation found in %s' % lookup_path
        )
