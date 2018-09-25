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
import glob
from collections import OrderedDict

# project
from kiwi.bootloader.config.base import BootLoaderConfigBase
from kiwi.bootloader.template.grub2 import BootLoaderTemplateGrub2
from kiwi.command import Command
from kiwi.defaults import Defaults
from kiwi.firmware import FirmWare
from kiwi.logger import log
from kiwi.path import Path
from kiwi.utils.sync import DataSync
from kiwi.utils.sysconfig import SysConfig

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderGrubPlatformError,
    KiwiBootLoaderGrubModulesError,
    KiwiBootLoaderGrubSecureBootError,
    KiwiBootLoaderGrubFontError,
    KiwiBootLoaderGrubDataError
)


class BootLoaderConfigGrub2(BootLoaderConfigBase):
    """
    **grub2 bootloader configuration.**
    """
    def post_init(self, custom_args):
        """
        grub2 post initialization method

        :param dict custom_args:
            Contains grub config arguments

            .. code:: python

                {'grub_directory_name': 'grub|grub2'}
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

        if self.custom_args and 'grub_directory_name' in self.custom_args:
            self.boot_directory_name = self.custom_args['grub_directory_name']
        else:
            self.boot_directory_name = 'grub'

        self.terminal = self.xml_state.build_type.get_bootloader_console() \
            or 'gfxterm'
        self.gfxmode = self.get_gfxmode('grub2')
        self.bootpath = self.get_boot_path()
        self.theme = self.get_boot_theme()
        self.timeout = self.get_boot_timeout_seconds()
        self.failsafe_boot = self.failsafe_boot_entry_requested()
        self.mediacheck_boot = self.xml_state.build_type.get_mediacheck()
        self.xen_guest = self.xml_state.is_xen_guest()
        self.firmware = FirmWare(
            self.xml_state
        )

        self.live_type = self.xml_state.build_type.get_flags()
        if not self.live_type:
            self.live_type = Defaults.get_default_live_iso_type()

        self.volume_id = self.xml_state.build_type.get_volid() or \
            Defaults.get_volume_id()
        self.install_volid = self.xml_state.build_type.get_volid() or \
            Defaults.get_install_volume_id()

        self.live_boot_options = [
            'root=live:CDLABEL={0}'.format(self.volume_id),
            'rd.live.image'
        ]
        self.install_boot_options = [
            'loglevel=0'
        ]
        if self.xml_state.get_initrd_system() == 'dracut':
            self.install_boot_options.append(
                'root=install:CDLABEL={0}'.format(self.install_volid)
            )
        if self.xml_state.build_type.get_hybridpersistent():
            self.live_boot_options += \
                Defaults.get_live_iso_persistent_boot_options(
                    self.xml_state.build_type.get_hybridpersistent_filesystem()
                )

        if self.xml_state.is_xen_server():
            self.hybrid_boot = False
            self.multiboot = True
        elif self.xen_guest:
            self.hybrid_boot = False
            self.multiboot = False
        else:
            self.hybrid_boot = True
            self.multiboot = False

        self.grub2 = BootLoaderTemplateGrub2()
        self.config = None
        self.efi_boot_path = None
        self.cmdline_failsafe = None
        self.cmdline = None
        self.iso_boot = False
        self.shim_fallback_setup = False

    def write(self):
        """
        Write grub.cfg and etc/default/grub file
        """
        config_dir = self._get_grub2_boot_path()
        config_file = config_dir + '/grub.cfg'
        if self.config:
            log.info('Writing grub.cfg file')
            Path.create(config_dir)
            with open(config_file, 'w') as config:
                config.write(self.config)

            if self.firmware.efi_mode():
                if self.iso_boot or self.shim_fallback_setup:
                    efi_vendor_boot_path = Defaults.get_shim_vendor_directory(
                        self.root_dir
                    )
                    if efi_vendor_boot_path:
                        grub_config_file_for_efi_boot = os.sep.join(
                            [efi_vendor_boot_path, 'grub.cfg']
                        )
                    else:
                        grub_config_file_for_efi_boot = os.path.normpath(
                            os.sep.join([self.efi_boot_path, 'grub.cfg'])
                        )
                    log.info(
                        'Writing {0} file to be found by EFI firmware'.format(
                            grub_config_file_for_efi_boot
                        )
                    )
                    with open(grub_config_file_for_efi_boot, 'w') as config:
                        config.write(self.config)

                if self.iso_boot:
                    self._create_embedded_fat_efi_image()

            self._setup_default_grub()
            self.setup_sysconfig_bootloader()

    def setup_sysconfig_bootloader(self):
        """
        Create or update etc/sysconfig/bootloader by the following
        parameters required according to the grub2 bootloader setup

        * LOADER_TYPE
        * LOADER_LOCATION
        * DEFAULT_APPEND
        * FAILSAFE_APPEND
        """
        sysconfig_bootloader_entries = {
            'LOADER_TYPE':
                'grub2-efi' if self.firmware.efi_mode() else 'grub2',
            'LOADER_LOCATION':
                'none' if self.firmware.efi_mode() else 'mbr'
        }
        if self.cmdline:
            sysconfig_bootloader_entries['DEFAULT_APPEND'] = '"{0}"'.format(
                self.cmdline
            )
        if self.cmdline_failsafe:
            sysconfig_bootloader_entries['FAILSAFE_APPEND'] = '"{0}"'.format(
                self.cmdline_failsafe
            )

        log.info('Writing sysconfig bootloader file')
        sysconfig_bootloader_location = ''.join(
            [self.root_dir, '/etc/sysconfig/']
        )
        if os.path.exists(sysconfig_bootloader_location):
            sysconfig_bootloader_file = ''.join(
                [sysconfig_bootloader_location, 'bootloader']
            )
            sysconfig_bootloader = SysConfig(
                sysconfig_bootloader_file
            )
            sysconfig_bootloader_entries_sorted = OrderedDict(
                sorted(sysconfig_bootloader_entries.items())
            )
            for key, value in list(sysconfig_bootloader_entries_sorted.items()):
                log.info('--> {0}:{1}'.format(key, value))
                sysconfig_bootloader[key] = value
            sysconfig_bootloader.write()

    def setup_disk_image_config(
        self, boot_uuid, root_uuid, hypervisor='xen.gz', kernel='linux.vmx',
        initrd='initrd.vmx', boot_options=''
    ):
        """
        Create the grub.cfg in memory from a template suitable to boot
        from a disk image

        :param string boot_uuid: boot device UUID
        :param string root_uuid: root device UUID
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
        :param string boot_options: kernel options as string
        """
        log.info('Creating grub2 config file from template')
        self.cmdline = ' '.join(
            [self.get_boot_cmdline(root_uuid), boot_options]
        )
        self.cmdline_failsafe = ' '.join(
            [self.cmdline, Defaults.get_failsafe_kernel_options(), boot_options]
        )
        parameters = {
            'search_params': ' '.join(['--fs-uuid', '--set=root', boot_uuid]),
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
            'boot_directory_name': self.boot_directory_name
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
        Create grub2 config file to boot from an ISO install image

        :param string mbrid: mbrid file name on boot device
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
        """
        log.info('Creating grub2 install config file from template')
        self.iso_boot = True
        self.cmdline = self.get_boot_cmdline()
        self.cmdline_failsafe = ' '.join(
            [self.cmdline, Defaults.get_failsafe_kernel_options()]
        )
        parameters = {
            'search_params': '--file --set=root /boot/' + mbrid.get_id(),
            'default_boot': self.get_install_image_boot_default(),
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': ' '.join(
                [self.cmdline] + self.install_boot_options
            ),
            'failsafe_boot_options': ' '.join(
                [self.cmdline_failsafe] + self.install_boot_options
            ),
            'gfxmode': self.gfxmode,
            'theme': self.theme,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_install_title(),
            'bootpath': '/boot/' + self.arch + '/loader',
            'boot_directory_name': self.boot_directory_name
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
        Create grub2 config file to boot a live media ISO image

        :param string mbrid: mbrid file name on boot device
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
        """
        log.info('Creating grub2 live ISO config file from template')
        self.iso_boot = True
        self.cmdline = self.get_boot_cmdline()
        self.cmdline_failsafe = ' '.join(
            [self.cmdline, Defaults.get_failsafe_kernel_options()]
        )
        parameters = {
            'search_params': '--file --set=root /boot/' + mbrid.get_id(),
            'default_boot': '0',
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': ' '.join(
                [self.cmdline] + self.live_boot_options
            ),
            'failsafe_boot_options': ' '.join(
                [self.cmdline_failsafe] + self.live_boot_options
            ),
            'gfxmode': self.gfxmode,
            'theme': self.theme,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_title(plain=True),
            'bootpath': '/boot/' + self.arch + '/loader',
            'boot_directory_name': self.boot_directory_name
        }
        if self.multiboot:
            log.info('--> Using multiboot template')
            parameters['hypervisor'] = hypervisor
            template = self.grub2.get_multiboot_iso_template(
                self.failsafe_boot, self.terminal, self.mediacheck_boot
            )
        else:
            log.info('--> Using standard boot template')
            hybrid_boot = True
            template = self.grub2.get_iso_template(
                self.failsafe_boot, hybrid_boot,
                self.terminal, self.mediacheck_boot
            )
        try:
            self.config = template.substitute(parameters)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def setup_install_boot_images(self, mbrid, lookup_path=None):
        """
        Create/Provide grub2 boot images and metadata

        In order to boot from the ISO grub2 modules, images and theme
        data needs to be created and provided at the correct place on
        the iso filesystem

        :param string mbrid: mbrid file name on boot device
        :param string lookup_path: custom module lookup path
        """
        log.info('Creating grub2 bootloader images')
        self.efi_boot_path = self.create_efi_path(in_sub_dir='')

        log.info('--> Creating identifier file %s', mbrid.get_id())
        Path.create(
            self._get_grub2_boot_path()
        )
        mbrid.write(
            self.root_dir + '/boot/' + mbrid.get_id()
        )
        mbrid.write(
            self.root_dir + '/boot/mbrid'
        )

        self._copy_theme_data_to_boot_directory(lookup_path)

        if self._supports_bios_modules():
            self._copy_bios_modules_to_boot_directory(lookup_path)

        if self.firmware.efi_mode():
            self._setup_EFI_path(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            self._setup_efi_image(mbrid=mbrid, lookup_path=lookup_path)
            self._copy_efi_modules_to_boot_directory(lookup_path)
        elif self.firmware.efi_mode() == 'uefi':
            self._copy_efi_modules_to_boot_directory(lookup_path)
            self._setup_secure_boot_efi_image(lookup_path)

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        """
        Create/Provide grub2 boot images and metadata

        Calls setup_install_boot_images because no different action required
        """
        self.setup_install_boot_images(mbrid, lookup_path)

    def setup_disk_boot_images(self, boot_uuid, lookup_path=None):
        """
        Create/Provide grub2 boot images and metadata

        In order to boot from the disk grub2 modules, images and theme
        data needs to be created and provided at the correct place in
        the filesystem

        :param string boot_uuid: boot device UUID
        :param string lookup_path: custom module lookup path
        """
        log.info('Creating grub2 bootloader images')

        if self.firmware.efi_mode():
            self.efi_boot_path = self.create_efi_path()

        self._copy_theme_data_to_boot_directory(lookup_path)

        if not self.xen_guest and self._supports_bios_modules():
            self._copy_bios_modules_to_boot_directory(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            self._setup_efi_image(uuid=boot_uuid, lookup_path=lookup_path)
            self._copy_efi_modules_to_boot_directory(lookup_path)
        elif self.firmware.efi_mode() == 'uefi':
            self._copy_efi_modules_to_boot_directory(lookup_path)
            if not self._get_shim_install():
                self.shim_fallback_setup = True
                self._setup_secure_boot_efi_image(lookup_path)

        if self.xen_guest:
            self._copy_xen_modules_to_boot_directory(lookup_path)

    def _supports_bios_modules(self):
        if self.arch == 'ix86' or self.arch == 'x86_64':
            return True
        return False

    def _setup_default_grub(self):
        """
        Create or update etc/default/grub by parameters required
        according to the root filesystem setup

        * GRUB_TIMEOUT
        * SUSE_BTRFS_SNAPSHOT_BOOTING
        * GRUB_BACKGROUND
        * GRUB_THEME
        * GRUB_USE_LINUXEFI
        * GRUB_USE_INITRDEFI
        * GRUB_SERIAL_COMMAND
        * GRUB_CMDLINE_LINUX_DEFAULT
        """
        grub_default_entries = {
            'GRUB_TIMEOUT': self.timeout
        }
        if self.cmdline:
            grub_default_entries['GRUB_CMDLINE_LINUX_DEFAULT'] = '"{0}"'.format(
                self.cmdline
            )
        if self.terminal and self.terminal == 'serial':
            serial_format = '"serial {0} {1} {2} {3} {4}"'
            grub_default_entries['GRUB_SERIAL_COMMAND'] = serial_format.format(
                '--speed=38400',
                '--unit=0',
                '--word=8',
                '--parity=no',
                '--stop=1'
            )
        if self.theme:
            theme_setup = '{0}/{1}/theme.txt'
            grub_default_entries['GRUB_THEME'] = theme_setup.format(
                ''.join(['/boot/', self.boot_directory_name, '/themes']),
                self.theme
            )
            theme_background = '{0}/{1}/background.png'.format(
                ''.join(['/boot/', self.boot_directory_name, '/themes']),
                self.theme
            )
            if os.path.exists(os.sep.join([self.root_dir, theme_background])):
                grub_default_entries['GRUB_BACKGROUND'] = theme_background
        if self.firmware.efi_mode():
            # linuxefi/initrdefi only exist on x86, others always use efi
            if self.arch == 'ix86' or self.arch == 'x86_64':
                grub_default_entries['GRUB_USE_LINUXEFI'] = 'true'
                grub_default_entries['GRUB_USE_INITRDEFI'] = 'true'
        if self.xml_state.build_type.get_btrfs_root_is_snapshot():
            grub_default_entries['SUSE_BTRFS_SNAPSHOT_BOOTING'] = 'true'

        if grub_default_entries:
            log.info('Writing grub2 defaults file')
            grub_default_location = ''.join([self.root_dir, '/etc/default/'])
            if os.path.exists(grub_default_location):
                grub_default_file = ''.join([grub_default_location, 'grub'])
                grub_default = SysConfig(grub_default_file)
                grub_default_entries_sorted = OrderedDict(
                    sorted(grub_default_entries.items())
                )
                for key, value in list(grub_default_entries_sorted.items()):
                    log.info('--> {0}:{1}'.format(key, value))
                    grub_default[key] = value
                grub_default.write()

    def _setup_secure_boot_efi_image(self, lookup_path):
        """
        Provide the shim loader and the shim signed grub2 loader
        in the required boot path. Normally this task is done by
        the shim-install tool. However, shim-install does not exist
        on all distributions and the script does not operate well
        in e.g CD environments from which we generate live and/or
        install media. Thus shim-install is used if possible at
        install time of the bootloader because it requires access
        to the target block device. In any other case this setup
        code should act as the fallback solution
        """
        log.warning(
            '--> Running fallback setup for shim secure boot efi image'
        )
        if not lookup_path:
            lookup_path = self.root_dir
        shim_image = Defaults.get_shim_loader(lookup_path)
        if not shim_image:
            raise KiwiBootLoaderGrubSecureBootError(
                'Microsoft signed shim loader not found'
            )
        grub_image = Defaults.get_signed_grub_loader(lookup_path)
        if not grub_image:
            raise KiwiBootLoaderGrubSecureBootError(
                'Shim signed grub2 efi loader not found'
            )
        Command.run(
            ['cp', shim_image, self._get_efi_image_name()]
        )
        Command.run(
            ['cp', grub_image, self.efi_boot_path]
        )

    def _setup_efi_image(self, uuid=None, mbrid=None, lookup_path=None):
        """
        Provide the unsigned grub2 efi image in the required boot path
        If a prebuilt efi image as provided by the distribution could
        be found, this image will be used. If no such image could be
        found we create a custom image with a pre defined set of
        grub modules
        """
        if not lookup_path:
            lookup_path = self.root_dir
        grub_image = Defaults.get_unsigned_grub_loader(lookup_path)
        if grub_image:
            log.info('--> Using prebuilt unsigned efi image')
            Command.run(
                ['cp', grub_image, self._get_efi_image_name()]
            )
            self._create_efi_config_search(uuid, mbrid)
        else:
            log.info('--> Creating unsigned efi image')
            self._create_efi_image(
                uuid, mbrid, lookup_path
            )

    def _create_embedded_fat_efi_image(self):
        Path.create(self.root_dir + '/boot/' + self.arch)
        efi_fat_image = ''.join(
            [self.root_dir + '/boot/', self.arch, '/efi']
        )
        Command.run(
            ['qemu-img', 'create', efi_fat_image, '15M']
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
                self._get_grub2_mkimage_tool() or 'grub2-mkimage',
                '-O', Defaults.get_efi_module_directory_name(self.arch),
                '-o', self._get_efi_image_name(),
                '-c', early_boot_script,
                '-p', self.get_boot_path() + '/' + self.boot_directory_name,
                '-d', self._get_efi_modules_path(lookup_path)
            ] + Defaults.get_grub_efi_modules(multiboot=self.xen_guest)
        )

    def _create_efi_config_search(self, uuid=None, mbrid=None):
        efi_boot_config = self.efi_boot_path + '/grub.cfg'
        if uuid:
            self._create_early_boot_script_for_uuid_search(
                efi_boot_config, uuid
            )
        else:
            self._create_early_boot_script_for_mbrid_search(
                efi_boot_config, mbrid
            )
        with open(efi_boot_config, 'a') as config:
            config.write('normal{0}'.format(os.linesep))

    def _create_early_boot_script_for_uuid_search(self, filename, uuid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'set btrfs_relative_path="yes"{0}'.format(os.linesep)
            )
            early_boot.write(
                'search --fs-uuid --set=root {0}{1}'.format(uuid, os.linesep)
            )
            early_boot.write(
                'set prefix=($root){0}/{1}{2}'.format(
                    self.get_boot_path(), self.boot_directory_name, os.linesep
                )
            )

    def _create_early_boot_script_for_mbrid_search(self, filename, mbrid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'set btrfs_relative_path="yes"{0}'.format(os.linesep)
            )
            early_boot.write(
                'search --file --set=root /boot/{0}{1}'.format(
                    mbrid.get_id(), os.linesep
                )
            )
            early_boot.write(
                'set prefix=($root)/boot/{0}{1}'.format(
                    self.boot_directory_name, os.linesep
                )
            )

    def _get_grub2_mkimage_tool(self):
        for grub_mkimage_tool in ['grub2-mkimage', 'grub-mkimage']:
            if Path.which(grub_mkimage_tool):
                return grub_mkimage_tool

    def _get_grub2_boot_path(self):
        return self.root_dir + '/boot/' + self.boot_directory_name

    def _get_efi_image_name(self):
        return self.efi_boot_path + '/' + Defaults.get_efi_image_name(self.arch)

    def _get_efi_modules_path(self, lookup_path=None):
        return self._get_module_path(
            Defaults.get_efi_module_directory_name(self.arch),
            lookup_path
        )

    def _get_bios_modules_path(self, lookup_path=None):
        return self._get_module_path('i386-pc', lookup_path)

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

    def _find_theme_background_file(self, lookup_path):
        background_pattern = os.sep.join(
            [
                lookup_path, 'boot', self.boot_directory_name, 'themes',
                '*', 'background.png'
            ]
        )
        for background_file in glob.iglob(background_pattern):
            return background_file

    def _copy_theme_data_to_boot_directory(self, lookup_path):
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
        Path.create(boot_theme_dir)

        if self.theme:
            theme_dir = self._find_grub_data(lookup_path + '/usr/share') + \
                '/themes/' + self.theme
            boot_theme_background_file = self._find_theme_background_file(
                lookup_path
            )
            if os.path.exists(theme_dir):
                if boot_theme_background_file:
                    # A background file was found. Preserve a copy of the
                    # file which was created at install time of the theme
                    # package by the activate-theme script
                    boot_theme_background_backup_file = os.sep.join(
                        [self.root_dir, 'background.png']
                    )
                    Command.run(
                        [
                            'cp', boot_theme_background_file,
                            boot_theme_background_backup_file
                        ]
                    )
                # sync theme data from install path to boot path
                data = DataSync(
                    theme_dir, boot_theme_dir
                )
                data.sync_data(
                    options=['-z', '-a']
                )
                if boot_theme_background_file:
                    # Install preserved background file to the theme
                    Command.run(
                        [
                            'mv', boot_theme_background_backup_file,
                            os.sep.join([boot_theme_dir, self.theme])
                        ]
                    )
            elif boot_theme_background_file:
                # assume all theme data is in the directory of the
                # background file and just sync that directory to the
                # boot path
                data = DataSync(
                    os.path.dirname(boot_theme_background_file), boot_theme_dir
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

    def _setup_EFI_path(self, lookup_path):
        """
        Copy efi boot data from lookup_path to the root directory
        """
        if not lookup_path:
            lookup_path = self.root_dir
        efi_path = lookup_path + '/boot/efi/'
        if os.path.exists(efi_path):
            efi_data = DataSync(efi_path, self.root_dir)
            efi_data.sync_data(options=['-a'])

    def _copy_efi_modules_to_boot_directory(self, lookup_path):
        self._copy_modules_to_boot_directory_from(
            self._get_efi_modules_path(lookup_path)
        )

    def _copy_bios_modules_to_boot_directory(self, lookup_path):
        self._copy_modules_to_boot_directory_from(
            self._get_bios_modules_path(lookup_path)
        )

    def _copy_xen_modules_to_boot_directory(self, lookup_path):
        self._copy_modules_to_boot_directory_from(
            self._get_xen_modules_path(lookup_path)
        )

    def _copy_modules_to_boot_directory_from(self, module_path):
        boot_module_path = \
            self._get_grub2_boot_path() + '/' + os.path.basename(module_path)
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

    def _get_shim_install(self):
        chroot_env = {
            'PATH': os.sep.join([self.root_dir, 'usr', 'sbin'])
        }
        return Path.which(
            filename='shim-install', custom_env=chroot_env
        )
