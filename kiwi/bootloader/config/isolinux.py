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
from ..template.isolinux import BootLoaderTemplateIsoLinux
from ...utils.sync import DataSync
from ...logger import log
from ...path import Path

from ...exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderIsoLinuxPlatformError
)


class BootLoaderConfigIsoLinux(BootLoaderConfigBase):
    """
        isolinux bootloader configuration.
    """
    def post_init(self, custom_args):
        self.custom_args = custom_args
        arch = platform.machine()
        if arch == 'x86_64':
            self.arch = arch
        elif arch == 'i686' or arch == 'i586':
            self.arch = 'ix86'
        else:
            raise KiwiBootLoaderIsoLinuxPlatformError(
                'host architecture %s not supported for isolinux setup' % arch
            )

        self.gfxmode = self.xml_state.build_type.get_vga()
        self.timeout = self.get_boot_timeout_seconds()
        self.cmdline = self.get_boot_cmdline()
        self.cmdline_failsafe = ' '.join(
            [self.cmdline, self.get_failsafe_kernel_options()]
        )
        self.failsafe_boot = self.failsafe_boot_entry_requested()
        self.hypervisor_domain = self.get_hypervisor_domain()

        self.multiboot = False
        if self.hypervisor_domain:
            if self.hypervisor_domain == 'dom0':
                self.multiboot = True
            elif self.hypervisor_domain == 'domU':
                self.multiboot = False

        self.isolinux = BootLoaderTemplateIsoLinux()
        self.config = None
        self.config_message = None

    def write(self):
        """
            Write isolinux.cfg and isolinux.msg file
        """
        log.info('Writing isolinux.cfg file')
        config_dir = self.__get_iso_boot_path()
        config_file = config_dir + '/isolinux.cfg'
        if self.config:
            Path.create(config_dir)
            with open(config_file, 'w') as config:
                config.write(self.config)

        config_file_message = config_dir + '/isolinux.msg'
        if self.config_message:
            with open(config_file_message, 'w') as config:
                config.write(self.config_message)

    def setup_install_image_config(
        self, mbrid, hypervisor='xen.gz', kernel='linux', initrd='initrd'
    ):
        """
            Create isolinux.cfg in memory from a template suitable to boot
            from an ISO image in BIOS boot mode
        """
        # mbrid parameter is not used, the information is placed as the
        # application id when creating the iso filesystem. Thus not part
        # of the configuration file
        log.info('Creating isolinux install config file from template')
        parameters = {
            'default_boot': 'Boot_from_Hard_Disk',
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': self.cmdline,
            'failsafe_boot_options': self.cmdline_failsafe,
            'gfxmode': self.gfxmode,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_install_title()
        }
        if self.multiboot:
            log.info('--> Using multiboot install template')
            parameters['hypervisor'] = hypervisor
            template = self.isolinux.get_multiboot_install_template(
                self.failsafe_boot, self.__have_theme()
            )
        else:
            log.info('--> Using install template')
            template = self.isolinux.get_install_template(
                self.failsafe_boot, self.__have_theme()
            )
        try:
            self.config = template.substitute(parameters)
            template = self.isolinux.get_install_message_template()
            self.config_message = template.substitute(parameters)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def setup_live_image_config(
        self, mbrid, hypervisor='xen.gz', kernel='linux', initrd='initrd'
    ):
        """
            Create isolinux.cfg in memory from a template suitable to boot
            a live system from an ISO image in BIOS boot mode
        """
        # mbrid parameter is not used, the information is placed as the
        # application id when creating the iso filesystem. Thus not part
        # of the configuration file
        log.info('Creating isolinux live ISO config file from template')
        parameters = {
            'default_boot': self.get_menu_entry_title(plain=True),
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': self.cmdline,
            'failsafe_boot_options': self.cmdline_failsafe,
            'gfxmode': self.gfxmode,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_title(plain=True)
        }
        if self.multiboot:
            log.info('--> Using multiboot standard ISO template')
            parameters['hypervisor'] = hypervisor
            template = self.isolinux.get_multiboot_template(
                self.failsafe_boot, self.__have_theme()
            )
        else:
            log.info('--> Using standard ISO template')
            template = self.isolinux.get_template(
                self.failsafe_boot, self.__have_theme()
            )
        try:
            self.config = template.substitute(parameters)
            template = self.isolinux.get_message_template()
            self.config_message = template.substitute(parameters)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def setup_install_boot_images(self, mbrid, lookup_path=None):
        # mbrid parameter is not used, because only isolinux loader
        # binary and possible theming files are copied
        self.__copy_loader_data_to_boot_directory(lookup_path)

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        # same action as for install media
        self.setup_install_boot_images(mbrid, lookup_path)

    def __copy_loader_data_to_boot_directory(self, lookup_path):
        if not lookup_path:
            lookup_path = self.root_dir
        loader_data = lookup_path + '/image/loader/'
        Path.create(self.__get_iso_boot_path())
        data = DataSync(
            loader_data, self.__get_iso_boot_path()
        )
        data.sync_data(
            options=['-z', '-a']
        )

    def __get_iso_boot_path(self):
        return self.root_dir + '/boot/' + self.arch + '/loader'

    def __have_theme(self):
        if os.path.exists(self.__get_iso_boot_path() + '/bootlogo'):
            return True
        return False
