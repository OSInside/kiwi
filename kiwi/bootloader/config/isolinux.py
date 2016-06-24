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
from ...defaults import Defaults

from ...exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderIsoLinuxPlatformError
)


class BootLoaderConfigIsoLinux(BootLoaderConfigBase):
    """
    isolinux bootloader configuration.

    Attributes

    * :attr:`terminal`
        terminal mode set to graphics by default

    * :attr:`gfxmode`
        configured or default graphics mode

    * :attr:`timeout`
        configured or default boot timeout

    * :attr:`cmdline`
        kernel boot arguments

    * :attr:`cmdline_failsafe`
        kernel failsafe boot arguments

    * :attr:`hypervisor_domain`
        configured hypervisor domain name or none

    * :attr:`multiboot`
        multiboot requested true|false

    * :attr:`isolinux`
        Instance of config template: BootLoaderTemplateIsoLinux

    * :attr:`config`
        Configuration data from template substitution

    * :attr:`config_message`
        Configuration text message if graphics mode failed
    """
    def post_init(self, custom_args):
        """
        isolinux post initialization method

        Setup class attributes
        """
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

        self.terminal = self.xml_state.build_type.get_bootloader_console()
        self.gfxmode = self.get_gfxmode('isolinux')
        self.timeout = self.get_boot_timeout_seconds()
        self.cmdline = self.get_boot_cmdline()
        self.cmdline_failsafe = ' '.join(
            [self.cmdline, Defaults.get_failsafe_kernel_options()]
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
        config_dir = self._get_iso_boot_path()
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

        :param string mbrid: mbrid file name on boot device
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
        """
        # mbrid parameter is not used, the information is placed as the
        # application id when creating the iso filesystem. Thus not part
        # of the configuration file
        log.info('Creating isolinux install config file from template')
        parameters = {
            'default_boot': self.get_install_image_boot_default('isolinux'),
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
                self.failsafe_boot, self._have_theme(), self.terminal
            )
        else:
            log.info('--> Using install template')
            template = self.isolinux.get_install_template(
                self.failsafe_boot, self._have_theme(), self.terminal
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

        :param string mbrid: mbrid file name on boot device
        :param string hypervisor: hypervisor name
        :param string kernel: kernel name
        :param string initrd: initrd name
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
                self.failsafe_boot, self._have_theme(), self.terminal
            )
        else:
            log.info('--> Using standard ISO template')
            template = self.isolinux.get_template(
                self.failsafe_boot, self._have_theme(), self.terminal
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
        """
        Provide isolinux boot metadata

        The mbrid parameter is not used, because only isolinux
        loader binary and possible theming files are copied

        :param string mbrid: unused
        :param string lookup_path: custom module lookup path
        """
        self._copy_loader_data_to_boot_directory(lookup_path)

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        """
        Provide isolinux boot metadata

        Calls setup_install_boot_images because no different action required
        """
        self.setup_install_boot_images(mbrid, lookup_path)

    def _copy_loader_data_to_boot_directory(self, lookup_path):
        if not lookup_path:
            lookup_path = self.root_dir
        loader_data = lookup_path + '/image/loader/'
        Path.create(self._get_iso_boot_path())
        data = DataSync(
            loader_data, self._get_iso_boot_path()
        )
        data.sync_data(
            options=['-z', '-a']
        )

    def _get_iso_boot_path(self):
        return self.root_dir + '/boot/' + self.arch + '/loader'

    def _have_theme(self):
        if os.path.exists(self._get_iso_boot_path() + '/bootlogo'):
            return True
        return False
