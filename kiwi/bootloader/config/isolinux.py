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

# project
from kiwi.bootloader.config.base import BootLoaderConfigBase
from kiwi.bootloader.template.isolinux import BootLoaderTemplateIsoLinux
from kiwi.path import Path
from kiwi.defaults import Defaults

from kiwi.exceptions import KiwiTemplateError

log = logging.getLogger('kiwi')


class BootLoaderConfigIsoLinux(BootLoaderConfigBase):
    """
    **isolinux bootloader configuration.**
    """
    def post_init(self, custom_args):
        """
        isolinux post initialization method

        :param dict custom_args: custom isolinux config arguments
        """
        self.custom_args = custom_args
        self.arch = Defaults.get_platform_name()

        self.install_volid = self.xml_state.build_type.get_volid() or \
            Defaults.get_install_volume_id()
        self.volume_id = self.xml_state.build_type.get_volid() or \
            Defaults.get_volume_id()

        self.live_type = self.xml_state.build_type.get_flags()
        if not self.live_type:
            self.live_type = Defaults.get_default_live_iso_type()

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

        self.terminal = self.xml_state.get_build_type_bootloader_console()
        self.gfxmode = self.get_gfxmode('isolinux')
        # isolinux counts the timeout in units of 1/10 sec
        self.timeout = self.get_boot_timeout_seconds() * 10
        self.continue_on_timeout = self.get_continue_on_timeout()
        self.cmdline = self.get_boot_cmdline()
        self.cmdline_failsafe = ' '.join(
            [self.cmdline, Defaults.get_failsafe_kernel_options()]
        )
        self.failsafe_boot = self.failsafe_boot_entry_requested()
        self.mediacheck_boot = self.xml_state.build_type.get_mediacheck()

        self.multiboot = False
        if self.xml_state.is_xen_server():
            self.multiboot = True

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
            'boot_options': ' '.join(
                [self.cmdline] + self.install_boot_options
            ),
            'failsafe_boot_options': ' '.join(
                [self.cmdline_failsafe] + self.install_boot_options
            ),
            'gfxmode': self.gfxmode,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_install_title()
        }
        if self.multiboot:
            log.info('--> Using multiboot install template')
            parameters['hypervisor'] = hypervisor
            template = self.isolinux.get_multiboot_install_template(
                self.failsafe_boot, self._have_theme(), self.terminal,
                self.continue_on_timeout
            )
        else:
            log.info('--> Using install template')
            template = self.isolinux.get_install_template(
                self.failsafe_boot, self._have_theme(), self.terminal,
                self.continue_on_timeout
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
            'boot_options': ' '.join(
                [self.cmdline] + self.live_boot_options
            ),
            'failsafe_boot_options': ' '.join(
                [self.cmdline_failsafe] + self.live_boot_options
            ),
            'gfxmode': self.gfxmode,
            'boot_timeout': self.timeout,
            'title': self.get_menu_entry_title(plain=True)
        }
        if self.multiboot:
            log.info('--> Using multiboot standard ISO template')
            parameters['hypervisor'] = hypervisor
            template = self.isolinux.get_multiboot_template(
                self.failsafe_boot, self._have_theme(),
                self.terminal, self.mediacheck_boot
            )
        else:
            log.info('--> Using standard ISO template')
            template = self.isolinux.get_template(
                self.failsafe_boot, self._have_theme(),
                self.terminal, self.mediacheck_boot
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

        No extra boot images must be created for isolinux

        :param string mbrid: unused
        :param string lookup_path: unused
        """
        pass

    def setup_live_boot_images(self, mbrid, lookup_path=None):
        """
        Provide isolinux boot metadata

        No extra boot images must be created for isolinux

        :param string mbrid: unused
        :param string lookup_path: unused
        """
        pass

    def _get_iso_boot_path(self):
        return self.boot_dir + '/boot/' + self.arch + '/loader'

    def _have_theme(self):
        if os.path.exists(self._get_iso_boot_path() + '/bootlogo'):
            return True
        return False
