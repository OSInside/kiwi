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
from string import Template
import re
import os
import logging
import glob
import shutil
from collections import OrderedDict

# project
from kiwi.bootloader.config.base import BootLoaderConfigBase
from kiwi.bootloader.template.grub2 import BootLoaderTemplateGrub2
from kiwi.command import Command
from kiwi.defaults import Defaults
from kiwi.firmware import FirmWare
from kiwi.path import Path
from kiwi.utils.sync import DataSync
from kiwi.utils.sysconfig import SysConfig

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderGrubPlatformError,
    KiwiBootLoaderGrubModulesError,
    KiwiBootLoaderGrubSecureBootError,
    KiwiBootLoaderGrubFontError,
    KiwiDiskGeometryError
)

log = logging.getLogger('kiwi')


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
        arch = Defaults.get_platform_name()
        if arch == 'x86_64':
            # grub2 support for bios and efi systems
            self.arch = arch
        elif arch.startswith('ppc64'):
            # grub2 support for ofw and opal systems
            self.arch = arch
        elif arch == 'ix86':
            # grub2 support for bios systems
            self.arch = arch
        elif arch == 'aarch64' or arch.startswith('arm'):
            # grub2 support for efi systems
            self.arch = arch
        elif arch.startswith('s390'):
            # grub2 support for s390x systems
            self.arch = arch
        else:
            raise KiwiBootLoaderGrubPlatformError(
                'host architecture %s not supported for grub2 setup' % arch
            )

        if self.custom_args and 'grub_directory_name' in self.custom_args:
            self.boot_directory_name = self.custom_args['grub_directory_name']
        else:
            self.boot_directory_name = 'grub'

        self.terminal = self.xml_state.get_build_type_bootloader_console() \
            or 'gfxterm'
        self.gfxmode = self.get_gfxmode('grub2')
        self.theme = self.get_boot_theme()
        self.timeout = self.get_boot_timeout_seconds()
        self.timeout_style = \
            self.xml_state.get_build_type_bootloader_timeout_style()
        self.displayname = self.xml_state.xml_data.get_displayname()
        self.serial_line_setup = \
            self.xml_state.get_build_type_bootloader_serial_line_setup()
        self.continue_on_timeout = self.get_continue_on_timeout()
        self.failsafe_boot = self.failsafe_boot_entry_requested()
        self.mediacheck_boot = self.xml_state.build_type.get_mediacheck()
        self.xen_guest = self.xml_state.is_xen_guest()
        self.firmware = FirmWare(
            self.xml_state
        )
        self.target_table_type = self.firmware.get_partition_table_type()

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
        self.root_reference = None
        self.cmdline = None
        self.iso_boot = False
        self.early_boot_script_efi = None

    def write(self):
        """
        Write bootloader configuration

        * writes grub.cfg template by KIWI if template system is used
        * creates an embedded fat efi image for EFI ISO boot
        """
        if self.config:
            log.info('Writing KIWI template grub.cfg file')
            config_dir = self._get_grub2_boot_path()
            config_file = config_dir + '/grub.cfg'
            Path.create(config_dir)
            with open(config_file, 'w') as config:
                config.write(self.config)

            if self.firmware.efi_mode():
                if self.iso_boot:
                    self._create_embedded_fat_efi_image()

    def write_meta_data(self, root_uuid=None, boot_options=''):
        """
        Write bootloader setup meta data files

        * cmdline arguments initialization
        * etc/default/grub setup file
        * etc/default/zipl2grub.conf.in (s390 only)
        * etc/sysconfig/bootloader

        :param string root_uuid: root device UUID
        :param string boot_options: kernel options as string
        :param bool iso_boot: indicate target is an ISO
        """
        self.cmdline = ' '.join(
            [self.get_boot_cmdline(root_uuid), boot_options]
        )
        self.cmdline_failsafe = ' '.join(
            [self.cmdline, Defaults.get_failsafe_kernel_options(), boot_options]
        )
        self.root_reference = self._get_root_cmdline_parameter(root_uuid)

        self._setup_default_grub()
        self._setup_sysconfig_bootloader()
        if self.arch.startswith('s390'):
            self._setup_zipl2grub_conf()

    def setup_disk_image_config(
        self, boot_uuid=None, root_uuid=None, hypervisor=None,
        kernel=None, initrd=None, boot_options={}
    ):
        """
        Create grub2 config file to boot from disk using grub2-mkconfig

        :param string boot_uuid: unused
        :param string root_uuid: unused
        :param string hypervisor: unused
        :param string kernel: unused
        :param string initrd: unused
        :param dict boot_options:

        options dictionary that has to contain the root and boot
        device and optional volume configuration. KIWI has to
        mount the system prior to run grub2-mkconfig.

        .. code:: python

            {
                'root_device': string,
                'boot_device': string,
                'efi_device': string,
                'system_volumes': volume_manager_instance.get_volumes()
            }
        """
        self._mount_system(
            boot_options.get('root_device'),
            boot_options.get('boot_device'),
            boot_options.get('efi_device'),
            boot_options.get('system_volumes')
        )
        config_file = os.sep.join(
            [
                self.root_mount.mountpoint, 'boot',
                self.boot_directory_name, 'grub.cfg'
            ]
        )
        Command.run(
            [
                'chroot', self.root_mount.mountpoint,
                os.path.basename(self._get_grub2_mkconfig_tool()), '-o',
                config_file.replace(self.root_mount.mountpoint, '')
            ]
        )
        if boot_options.get('root_device') != boot_options.get('boot_device'):
            # Create a boot -> . link on the boot partition.
            # The link is useful if the grub mkconfig command
            # references all boot files from /boot/... even if
            # an extra boot partition should cause it to read the
            # data from the toplevel
            bash_command = [
                'cd', os.sep.join([self.root_mount.mountpoint, 'boot']), '&&',
                'rm', '-f', 'boot', '&&',
                'ln', '-s', '.', 'boot'
            ]
            Command.run(
                ['bash', '-c', ' '.join(bash_command)]
            )

        # Patch the written grub config file to actually work:
        # Unfortunately the grub tooling has several bugs and issues
        # which prevents it to work in image build environments.
        # More details can be found in the individual methods.
        # One fine day the following fix methods can hopefully
        # be deleted...
        self._fix_grub_to_support_dynamic_efi_and_bios_boot(config_file)
        self._fix_grub_root_device_reference(config_file, boot_options)
        self._fix_grub_loader_entries_boot_cmdline()

        if self.firmware.efi_mode() and self.early_boot_script_efi:
            self._copy_grub_config_to_efi_path(
                self.efi_mount.mountpoint, self.early_boot_script_efi
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
            'boot_timeout_style': self.timeout_style or 'menu',
            'serial_line_setup': self.serial_line_setup or 'serial',
            'title': self.get_menu_entry_install_title(),
            'bootpath': self.get_boot_path('iso'),
            'boot_directory_name': self.boot_directory_name,
            'efi_image_name': Defaults.get_efi_image_name(self.arch),
            'terminal_setup': self.terminal
        }
        if self.multiboot:
            log.info('--> Using multiboot install template')
            parameters['hypervisor'] = hypervisor
            template = self.grub2.get_multiboot_install_template(
                self.failsafe_boot, self.terminal,
                self.continue_on_timeout
            )
        else:
            log.info('--> Using standard boot install template')
            hybrid_boot = True
            template = self.grub2.get_install_template(
                self.failsafe_boot, hybrid_boot, self.terminal,
                self.continue_on_timeout
            )
        try:
            self.config = template.substitute(parameters)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        if self.firmware.efi_mode() and self.early_boot_script_efi:
            self._copy_grub_config_to_efi_path(
                self.boot_dir, self.early_boot_script_efi
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
            'boot_timeout_style': self.timeout_style or 'menu',
            'serial_line_setup': self.serial_line_setup or 'serial',
            'title': self.get_menu_entry_title(plain=True),
            'bootpath': self.get_boot_path('iso'),
            'boot_directory_name': self.boot_directory_name,
            'efi_image_name': Defaults.get_efi_image_name(self.arch),
            'terminal_setup': self.terminal
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
        if self.firmware.efi_mode() and self.early_boot_script_efi:
            self._copy_grub_config_to_efi_path(
                self.boot_dir, self.early_boot_script_efi
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
            self.boot_dir + '/boot/' + mbrid.get_id()
        )
        mbrid.write(
            self.boot_dir + '/boot/mbrid'
        )

        self._copy_theme_data_to_boot_directory(lookup_path, 'iso')

        if self._supports_bios_modules():
            self._copy_bios_modules_to_boot_directory(lookup_path)
            self._setup_bios_image(mbrid=mbrid, lookup_path=lookup_path)

        if self.firmware.efi_mode():
            self._setup_EFI_path(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            self._setup_efi_image(mbrid=mbrid, lookup_path=lookup_path)
            self._copy_efi_modules_to_boot_directory(lookup_path)
        elif self.firmware.efi_mode() == 'uefi':
            self._copy_efi_modules_to_boot_directory(lookup_path)
            self._setup_secure_boot_efi_image(
                lookup_path=lookup_path, mbrid=mbrid
            )

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

        self._copy_theme_data_to_boot_directory(lookup_path, 'disk')

        if not self.xen_guest and self._supports_bios_modules():
            self._copy_bios_modules_to_boot_directory(lookup_path)

        if self.firmware.efi_mode() == 'efi':
            self._setup_efi_image(uuid=boot_uuid, lookup_path=lookup_path)
            self._copy_efi_modules_to_boot_directory(lookup_path)
        elif self.firmware.efi_mode() == 'uefi':
            self._copy_efi_modules_to_boot_directory(lookup_path)
            if not self._get_shim_install():
                self._setup_secure_boot_efi_image(
                    lookup_path=lookup_path, uuid=boot_uuid
                )

        if self.xen_guest:
            self._copy_xen_modules_to_boot_directory(lookup_path)

    def _copy_grub_config_to_efi_path(self, root_path, config_file):
        efi_boot_path = Defaults.get_shim_vendor_directory(
            root_path
        )
        if not efi_boot_path:
            efi_boot_path = os.path.normpath(
                os.sep.join([root_path, 'EFI/BOOT'])
            )
        Path.create(efi_boot_path)
        grub_config_file_for_efi_boot = os.sep.join(
            [efi_boot_path, 'grub.cfg']
        )
        if config_file != grub_config_file_for_efi_boot:
            log.info(
                'Copying {0} -> {1} to be found by EFI'.format(
                    config_file, grub_config_file_for_efi_boot
                )
            )
            shutil.copy(
                config_file, grub_config_file_for_efi_boot
            )

    def _supports_bios_modules(self):
        if self.arch == 'ix86' or self.arch == 'x86_64':
            return True
        return False

    def _setup_sysconfig_bootloader(self):
        """
        Create or update etc/sysconfig/bootloader by the following
        parameters required according to the grub2 bootloader setup

        * LOADER_TYPE
        * LOADER_LOCATION
        * DEFAULT_APPEND
        * FAILSAFE_APPEND
        * SECURE_BOOT
        """
        sysconfig_bootloader_entries = {
            'LOADER_TYPE':
                'grub2-efi' if self.firmware.efi_mode() else 'grub2',
            'LOADER_LOCATION':
                'none' if self.firmware.efi_mode() else 'mbr'
        }
        if self.firmware.efi_mode() == 'uefi':
            sysconfig_bootloader_entries['SECURE_BOOT'] = 'yes'
        if self.cmdline:
            sysconfig_bootloader_entries['DEFAULT_APPEND'] = '"{0}"'.format(
                self.cmdline
            )
        if self.cmdline_failsafe:
            sysconfig_bootloader_entries['FAILSAFE_APPEND'] = '"{0}"'.format(
                self.cmdline_failsafe
            )

        sysconfig_bootloader_location = ''.join(
            [self.root_dir, '/etc/sysconfig/']
        )
        if os.path.exists(sysconfig_bootloader_location):
            log.info('Writing sysconfig bootloader file')
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

    def _setup_zipl2grub_conf(self):
        zipl2grub_config_file = ''.join(
            [self.root_dir, '/etc/default/zipl2grub.conf.in']
        )
        zipl2grub_config_file_orig = ''.join(
            [self.root_dir, '/etc/default/zipl2grub.conf.in.orig']
        )
        target_type = self.xml_state.get_build_type_bootloader_targettype()
        target_blocksize = self.xml_state.build_type.get_target_blocksize()
        if target_type and os.path.exists(zipl2grub_config_file):
            if os.path.exists(zipl2grub_config_file_orig):
                # reset the original template file first
                shutil.copy(zipl2grub_config_file_orig, zipl2grub_config_file)
            else:
                # no copy of the original template, create it
                shutil.copy(zipl2grub_config_file, zipl2grub_config_file_orig)
            with open(zipl2grub_config_file) as zipl_config_file:
                zipl_config = zipl_config_file.read()
                zipl_config = re.sub(
                    r'(:menu)',
                    ':menu\n'
                    '    targettype = {0}\n'
                    '    targetbase = {1}\n'
                    '    targetblocksize = {2}\n'
                    '    targetoffset = {3}\n'
                    '    {4}'.format(
                        target_type,
                        self.custom_args['targetbase'],
                        target_blocksize or 512,
                        self._get_partition_start(
                            self.custom_args['targetbase']
                        ),
                        self._get_disk_geometry(
                            self.custom_args['targetbase']
                        )
                    ),
                    zipl_config
                )
            log.debug('Updated zipl template as follows')
            with open(zipl2grub_config_file, 'w') as zipl_config_file:
                log.debug(zipl_config)
                zipl_config_file.write(zipl_config)

    def _setup_default_grub(self):
        """
        Create or update etc/default/grub by parameters required
        according to the root filesystem setup

        * GRUB_TIMEOUT
        * GRUB_TIMEOUT_STYLE
        * SUSE_BTRFS_SNAPSHOT_BOOTING
        * GRUB_BACKGROUND
        * GRUB_THEME
        * GRUB_USE_LINUXEFI
        * GRUB_USE_INITRDEFI
        * GRUB_SERIAL_COMMAND
        * GRUB_CMDLINE_LINUX_DEFAULT
        * GRUB_GFXMODE
        * GRUB_TERMINAL
        * GRUB_DISTRIBUTOR
        """
        grub_default_entries = {
            'GRUB_TIMEOUT': self.timeout,
            'GRUB_GFXMODE': self.gfxmode,
            'GRUB_TERMINAL': '"{0}"'.format(self.terminal)
        }
        grub_final_cmdline = re.sub(
            r'root=.* |root=.*$', '', self.cmdline
        ).strip()
        if self.displayname:
            grub_default_entries['GRUB_DISTRIBUTOR'] = '"{0}"'.format(
                self.displayname
            )
        if self.timeout_style:
            grub_default_entries['GRUB_TIMEOUT_STYLE'] = self.timeout_style
        if grub_final_cmdline:
            grub_default_entries['GRUB_CMDLINE_LINUX_DEFAULT'] = '"{0}"'.format(
                grub_final_cmdline
            )
        if self.terminal and 'serial' in self.terminal and \
           self.serial_line_setup:
            grub_default_entries['GRUB_SERIAL_COMMAND'] = '"{0}"'.format(
                self.serial_line_setup
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
                use_linuxefi_implemented = Command.run(
                    [
                        'grep', '-q', 'GRUB_USE_LINUXEFI',
                        self._get_grub2_mkconfig_tool()
                    ], raise_on_error=False
                )
                if use_linuxefi_implemented.returncode == 0:
                    grub_default_entries['GRUB_USE_LINUXEFI'] = 'true'
                    grub_default_entries['GRUB_USE_INITRDEFI'] = 'true'
        if self.xml_state.build_type.get_btrfs_root_is_snapshot():
            grub_default_entries['SUSE_BTRFS_SNAPSHOT_BOOTING'] = 'true'
        if self.custom_args.get('boot_is_crypto'):
            grub_default_entries['GRUB_ENABLE_CRYPTODISK'] = 'y'

        enable_blscfg_implemented = Command.run(
            [
                'grep', '-q', 'GRUB_ENABLE_BLSCFG',
                self._get_grub2_mkconfig_tool()
            ], raise_on_error=False
        )
        if enable_blscfg_implemented.returncode == 0:
            grub_default_entries['GRUB_ENABLE_BLSCFG'] = 'true'

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

    def _setup_secure_boot_efi_image(self, lookup_path, uuid=None, mbrid=None):
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
            lookup_path = self.boot_dir
        grub_image = Defaults.get_signed_grub_loader(lookup_path)
        if not grub_image:
            raise KiwiBootLoaderGrubSecureBootError(
                'Signed grub2 efi loader not found'
            )
        shim_image = Defaults.get_shim_loader(lookup_path)
        if shim_image:
            # The shim concept is based on a two step system including a
            # grub image(shim) that got signed by Microsoft followed by
            # a grub image that got signed by the shim. The shim image
            # is the one that gets loaded by the firmware which itself
            # loads the second stage grub image
            Command.run(
                ['cp', shim_image, self._get_efi_image_name()]
            )
            Command.run(
                ['cp', grub_image, self.efi_boot_path]
            )
        else:
            # Without shim a self signed grub image is used that
            # gets loaded by the firmware
            Command.run(
                ['cp', grub_image, self._get_efi_image_name()]
            )
        self._create_efi_config_search(uuid, mbrid)

    def _setup_efi_image(self, uuid=None, mbrid=None, lookup_path=None):
        """
        Provide the unsigned grub2 efi image in the required boot path
        If a prebuilt efi image as provided by the distribution could
        be found, this image will be used. If no such image could be
        found we create a custom image with a pre defined set of
        grub modules
        """
        if not lookup_path:
            lookup_path = self.boot_dir
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

    def _setup_bios_image(self, mbrid=None, lookup_path=None):
        """
        Provide bios grub image
        """
        if not lookup_path:
            lookup_path = self.boot_dir
        grub_image = Defaults.get_grub_bios_core_loader(lookup_path)
        if grub_image:
            log.info('--> Using prebuilt bios image')
        else:
            log.info('--> Creating bios image')
            self._create_bios_image(
                mbrid, lookup_path
            )
        bash_command = ' '.join(
            [
                'cat',
                self._get_bios_modules_path(lookup_path) + '/cdboot.img',
                grub_image or self._get_bios_image_name(lookup_path),
                '>',
                os.sep.join(
                    [
                        self._get_bios_modules_path(lookup_path),
                        Defaults.get_isolinux_bios_grub_loader()
                    ]
                )
            ]
        )
        Command.run(
            ['bash', '-c', bash_command]
        )

    def _create_embedded_fat_efi_image(self):
        Path.create(self.boot_dir + '/boot/' + self.arch)
        efi_fat_image = ''.join(
            [self.boot_dir + '/boot/', self.arch, '/efi']
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
                self.boot_dir + '/EFI', '::'
            ]
        )

    def _create_efi_image(self, uuid=None, mbrid=None, lookup_path=None):
        early_boot_script = os.path.normpath(
            os.sep.join([self.efi_boot_path, 'earlyboot.cfg'])
        )
        self.early_boot_script_efi = early_boot_script
        if uuid:
            self._create_early_boot_script_for_uuid_search(
                early_boot_script, uuid
            )
        else:
            self._create_early_boot_script_for_mbrid_search(
                early_boot_script, mbrid
            )
        module_list = Defaults.get_grub_efi_modules(multiboot=self.xen_guest)
        module_path = self._get_efi_modules_path(lookup_path)
        if os.path.exists(module_path + '/linuxefi.mod'):
            module_list.append('linuxefi')
        Command.run(
            [
                self._get_grub2_mkimage_tool() or 'grub2-mkimage',
                '-O', Defaults.get_efi_module_directory_name(self.arch),
                '-o', self._get_efi_image_name(),
                '-c', early_boot_script,
                '-p', self.get_boot_path() + '/' + self.boot_directory_name,
                '-d', module_path
            ] + module_list
        )

    def _create_efi_config_search(self, uuid=None, mbrid=None):
        efi_boot_config = self.efi_boot_path + '/grub.cfg'
        self.early_boot_script_efi = efi_boot_config
        if uuid:
            self._create_early_boot_script_for_uuid_search(
                efi_boot_config, uuid
            )
        else:
            self._create_early_boot_script_for_mbrid_search(
                efi_boot_config, mbrid
            )

    def _create_bios_image(self, mbrid=None, lookup_path=None):
        early_boot_script = os.path.normpath(
            os.sep.join([self._get_grub2_boot_path(), 'earlyboot.cfg'])
        )
        self._create_early_boot_script_for_mbrid_search(
            early_boot_script, mbrid
        )
        Command.run(
            [
                self._get_grub2_mkimage_tool() or 'grub2-mkimage',
                '-O', Defaults.get_bios_module_directory_name(),
                '-o', self._get_bios_image_name(lookup_path),
                '-c', early_boot_script,
                '-p', self.get_boot_path() + '/' + self.boot_directory_name,
                '-d', self._get_bios_modules_path(lookup_path)
            ] + Defaults.get_grub_bios_modules(multiboot=self.xen_guest)
        )

    def _create_early_boot_script_for_uuid_search(self, filename, uuid):
        with open(filename, 'w') as early_boot:
            early_boot.write(
                'set btrfs_relative_path="yes"{0}'.format(os.linesep)
            )
            if self.custom_args.get('boot_is_crypto'):
                early_boot.write(
                    'insmod cryptodisk{0}'.format(os.linesep)
                )
                early_boot.write(
                    'insmod luks{0}'.format(os.linesep)
                )
                early_boot.write(
                    'cryptomount -u {0}{1}'.format(
                        uuid.replace('-', ''), os.linesep
                    )
                )
                early_boot.write(
                    'set root="cryptouuid/{0}"{1}'.format(
                        uuid.replace('-', ''), os.linesep
                    )
                )
            early_boot.write(
                'search --fs-uuid --set=root {0}{1}'.format(uuid, os.linesep)
            )
            early_boot.write(
                'set prefix=($root){0}/{1}{2}'.format(
                    self.get_boot_path(), self.boot_directory_name, os.linesep
                )
            )
            early_boot.write(
                'configfile ($root){0}/{1}/grub.cfg{2}'.format(
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
            early_boot.write(
                'configfile ($root)/boot/{0}/grub.cfg{1}'.format(
                    self.boot_directory_name, os.linesep
                )
            )

    def _get_grub2_mkimage_tool(self):
        for grub_mkimage_tool in ['grub2-mkimage', 'grub-mkimage']:
            if Path.which(grub_mkimage_tool):
                return grub_mkimage_tool

    def _get_grub2_mkconfig_tool(self):
        for grub_mkconfig_tool in ['grub2-mkconfig', 'grub-mkconfig']:
            grub_mkconfig_file_path = Path.which(
                grub_mkconfig_tool, root_dir=self.root_dir
            )
            if grub_mkconfig_file_path:
                return grub_mkconfig_file_path

    def _get_grub2_boot_path(self):
        return self.boot_dir + '/boot/' + self.boot_directory_name

    def _get_efi_image_name(self):
        return os.sep.join(
            [
                self.efi_boot_path,
                Defaults.get_efi_image_name(self.arch)
            ]
        )

    def _get_bios_image_name(self, lookup_path):
        return os.sep.join(
            [
                self._get_bios_modules_path(lookup_path),
                Defaults.get_bios_image_name()
            ]
        )

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
            lookup_path = self.boot_dir
        return Defaults.get_grub_path(lookup_path, format_name)

    def _find_theme_background_file(self, lookup_path):
        background_pattern = os.sep.join(
            [
                lookup_path, 'boot', self.boot_directory_name, 'themes',
                '*', 'background.png'
            ]
        )
        for background_file in glob.iglob(background_pattern):
            return background_file

    def _copy_theme_data_to_boot_directory(self, lookup_path, target):
        if not lookup_path:
            lookup_path = self.boot_dir
        font_name = 'unicode.pf2'
        efi_font_dir = Defaults.get_grub_efi_font_directory(
            lookup_path
        )
        boot_fonts_dir = os.path.normpath(
            os.sep.join(
                [
                    self.boot_dir,
                    self.get_boot_path(target),
                    self.boot_directory_name,
                    'fonts'
                ]
            )
        )
        try:
            unicode_font = Defaults.get_grub_path(
                lookup_path, font_name
            )
            if not os.path.exists(os.sep.join([boot_fonts_dir, font_name])):
                Path.create(boot_fonts_dir)
                Command.run(
                    ['cp', unicode_font, boot_fonts_dir]
                )
            if efi_font_dir:
                Command.run(
                    ['cp', unicode_font, efi_font_dir]
                )
        except Exception as issue:
            raise KiwiBootLoaderGrubFontError(
                'Setting up unicode font failed with {0}'.format(issue)
            )

        boot_theme_dir = os.sep.join(
            [self.boot_dir, 'boot', self.boot_directory_name, 'themes']
        )
        Path.create(boot_theme_dir)

        if self.theme:
            theme_dir = Defaults.get_grub_path(
                lookup_path, 'themes/' + self.theme, raise_on_error=False
            )
            boot_theme_background_file = self._find_theme_background_file(
                lookup_path
            )
            if theme_dir and os.path.exists(theme_dir):
                if boot_theme_background_file:
                    # A background file was found. Preserve a copy of the
                    # file which was created at install time of the theme
                    # package by the activate-theme script
                    boot_theme_background_backup_file = os.sep.join(
                        [self.boot_dir, 'background.png']
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
                    options=['-a']
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
                    options=['-a']
                )

        self._check_boot_theme_exists()

    def _check_boot_theme_exists(self):
        if self.theme:
            theme_dir = os.sep.join(
                [
                    self.boot_dir, 'boot', self.boot_directory_name,
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
            lookup_path = self.boot_dir
        efi_path = lookup_path + '/boot/efi/'
        if os.path.exists(efi_path):
            efi_data = DataSync(efi_path, self.boot_dir)
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
                options=['-a'], exclude=['*.module']
            )
        except Exception as e:
            raise KiwiBootLoaderGrubModulesError(
                'Module synchronisation failed with: %s' % format(e)
            )

    def _get_shim_install(self):
        return Path.which(
            filename='shim-install', root_dir=self.boot_dir
        )

    def _fix_grub_to_support_dynamic_efi_and_bios_boot(self, config_file):
        if self.firmware.efi_mode():
            # On systems that are configured to use EFI with grub2
            # there is no support for dynamic EFI environment checking.
            # In this condition we change the grub config to add this
            # support as follows:
            #
            # * Apply on grub with EFI
            #    1. Modify grub.cfg to set linux/initrd as variables
            #    2. Prepend hybrid setup to select linux vs. linuxefi on demand
            #
            # Please note this is a one time modification done by kiwi
            # Any subsequent call of the grub config tool will overwrite
            # the setup and disables dynamic EFI environment checking
            # at boot time
            with open(config_file) as grub_config_file:
                grub_config = grub_config_file.read()
                grub_config = re.sub(
                    r'([ \t]+)linux(efi|16)*([ \t]+)', r'\1$linux\3',
                    grub_config
                )
                grub_config = re.sub(
                    r'([ \t]+)initrd(efi|16)*([ \t]+)', r'\1$initrd\3',
                    grub_config
                )
            with open(config_file, 'w') as grub_config_file:
                grub_config_file.write(
                    Template(self.grub2.header_hybrid).substitute()
                )
                grub_config_file.write(grub_config)

    def _fix_grub_root_device_reference(self, config_file, boot_options):
        if self.root_reference:
            if self.root_filesystem_is_overlay or \
               self.arch.startswith('s390') or \
               Defaults.is_buildservice_worker():
                # grub2-mkconfig has no idea how the correct root= setup is
                # for disk images created with overlayroot enabled or in a
                # buildservice worker environment. Because of that the mkconfig
                # tool just finds the raw partition loop device and includes it
                # which is wrong. In this particular case we have to patch the
                # written config file and replace the wrong root= reference with
                # the correct value.
                with open(config_file) as grub_config_file:
                    grub_config = grub_config_file.read()
                    # The following expression matches any of the following
                    # grub mkconfig root= settings and replaces it with a
                    # correct value
                    # 1. root=LOCAL-KIWI-MAPPED-DEVICE
                    # 2. root=[a-zA-Z]=ANY-LINUX-BY-ID-VALUE
                    grub_config = re.sub(
                        r'(root=[a-zA-Z]+=[a-zA-Z0-9:\.-]+)|(root={0})'.format(
                            boot_options.get('root_device')
                        ),
                        '{0}'.format(self.root_reference),
                        grub_config
                    )

                with open(config_file, 'w') as grub_config_file:
                    grub_config_file.write(grub_config)

                if self.firmware.efi_mode():
                    vendor_grubenv_file = \
                        Defaults.get_vendor_grubenv(self.efi_mount.mountpoint)
                    if vendor_grubenv_file:
                        with open(vendor_grubenv_file) as vendor_grubenv:
                            grubenv = vendor_grubenv.read()
                            grubenv = grubenv.replace(
                                'root={0}'.format(
                                    boot_options.get('root_device')
                                ),
                                self.root_reference
                            )
                        with open(vendor_grubenv_file, 'w') as vendor_grubenv:
                            vendor_grubenv.write(grubenv)

    def _fix_grub_loader_entries_boot_cmdline(self):
        if self.cmdline:
            # For distributions that follows the bootloader spec here:
            # https://www.freedesktop.org/wiki/Specifications/BootLoaderSpec
            # the menu entries are managed in extra files written to
            # boot/loader/entries. The grub2-mkconfig tool imports the
            # information from there and has no own menu entries data
            # in grub.cfg anymore. Unfortunately the system that writes
            # those new boot/loader/entries has several issues. It produces
            # a complete mess when used in chroot environments. In such
            # an environment it takes the proc/cmdline data from the host
            # that built the image and completely ignores the setup of
            # the image description. Overall for image building the
            # tooling is completely broken and we are forced to patch the
            # entire cmdline for the menuentries on such systems.
            loader_entries_pattern = os.sep.join(
                [
                    self.root_mount.mountpoint,
                    'boot', 'loader', 'entries', '*.conf'
                ]
            )
            for menu_entry_file in glob.iglob(loader_entries_pattern):
                with open(menu_entry_file) as grub_menu_entry_file:
                    menu_entry = grub_menu_entry_file.read()
                    menu_entry = re.sub(
                        r'options (.*)',
                        r'options {0}'.format(self.cmdline),
                        menu_entry
                    )
                with open(menu_entry_file, 'w') as grub_menu_entry_file:
                    grub_menu_entry_file.write(menu_entry)

    def _get_partition_start(self, disk_device):
        if self.target_table_type == 'dasd':
            blocks = self._get_dasd_disk_geometry_element(
                disk_device, 'blocks per track'
            )
            bash_command = [
                'fdasd', '-f', '-s', '-p', disk_device,
                '|', 'grep', '"^ "',
                '|', 'head', '-n', '1',
                '|', 'tr', '-s', '" "'
            ]
            fdasd_call = Command.run(
                ['bash', '-c', ' '.join(bash_command)]
            )
            fdasd_output = fdasd_call.output
            try:
                start_track = int(fdasd_output.split(' ')[2].lstrip())
            except Exception:
                raise KiwiDiskGeometryError(
                    'unknown partition format: %s' % fdasd_output
                )
            return '{0}'.format(start_track * blocks)
        else:
            bash_command = ' '.join(
                [
                    'sfdisk', '--dump', disk_device,
                    '|', 'grep', '"1 :"',
                    '|', 'cut', '-f1', '-d,',
                    '|', 'cut', '-f2', '-d='
                ]
            )
            return Command.run(
                ['bash', '-c', bash_command]
            ).output.strip()

    def _get_disk_geometry(self, disk_device):
        disk_geometry = ''
        if self.target_table_type == 'dasd':
            disk_geometry = 'targetgeometry = {0},{1},{2}'.format(
                self._get_dasd_disk_geometry_element(
                    disk_device, 'cylinders'
                ),
                self._get_dasd_disk_geometry_element(
                    disk_device, 'tracks per cylinder'
                ),
                self._get_dasd_disk_geometry_element(
                    disk_device, 'blocks per track'
                )
            )
        return disk_geometry

    def _get_dasd_disk_geometry_element(self, disk_device, search):
        fdasd = ['fdasd', '-f', '-p', disk_device]
        bash_command = fdasd + ['|', 'grep', '"' + search + '"']
        fdasd_call = Command.run(
            ['bash', '-c', ' '.join(bash_command)]
        )
        fdasd_output = fdasd_call.output
        try:
            return int(fdasd_output.split(':')[1].lstrip())
        except Exception:
            raise KiwiDiskGeometryError(
                'unknown format for disk geometry: %s' % fdasd_output
            )
