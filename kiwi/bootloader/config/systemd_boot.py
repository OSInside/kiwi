# Copyright (c) 2022 Marcus Schäfer
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
from string import Template
from typing import Dict

# project
from kiwi.path import Path
from kiwi.bootloader.template.systemd_boot import BootLoaderTemplateSystemdBoot
from kiwi.bootloader.config.bootloader_spec_base import BootLoaderSpecBase
from kiwi.boot.image.base import BootImageBase
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderTargetError
)


class BootLoaderSystemdBoot(BootLoaderSpecBase):
    def create_loader_image(self, target: str) -> None:
        """
        Handle EFI images

        For systemd boot EFI images are provided along with systemd.
        Thus the only action taken care of is the creation of the
        ESP path

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)
        """
        self.efi_boot_path = self.create_efi_path()

    def setup_loader(self, target: str) -> None:
        """
        Setup ESP for systemd-boot using bootctl and kernel-install

        For disk images only, setup the ESP layout for systemd boot
        using bootctl. All data will be loaded from the ESP. The
        kernel-install script provided with systemd is used to
        manage kernel updates and the respective loader entries.
        Distributions integrating well with systemd runs kernel-install
        as part of their kernel packaging. In kiwi we use kernel-install
        for the initial boot setup

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)
            Currently only the disk identifier is supported
        """
        if target != self.target.disk:
            raise KiwiBootLoaderTargetError(
                'systemd-boot is only supported with the EFI disk image target'
            )
        boot_options = self.custom_args['boot_options']
        self._mount_system(
            boot_options.get('root_device'),
            boot_options.get('boot_device'),
            boot_options.get('efi_device'),
            boot_options.get('system_volumes')
        )
        kernel_info = BootImageBase(
            self.xml_state,
            self.root_mount.mountpoint, self.root_mount.mountpoint
        ).get_boot_names()
        Command.run(
            [
                'chroot', self.root_mount.mountpoint, 'bootctl', 'install',
                '--esp-path=/boot/efi',
                '--no-variables',
                '--entry-token', 'os-id'
            ]
        )
        Path.wipe(f'{self.root_mount.mountpoint}/boot/loader')
        self._write_kernel_cmdline_file()
        Command.run(
            [
                'chroot', self.root_mount.mountpoint,
                'kernel-install', 'add', kernel_info.kernel_version,
                kernel_info.kernel_filename.replace(
                    self.root_mount.mountpoint, ''
                ),
                f'/boot/{kernel_info.initrd_name}'
            ]
        )
        BootLoaderSystemdBoot._write_config_file(
            BootLoaderTemplateSystemdBoot().get_loader_template(),
            self.root_mount.mountpoint + '/boot/efi/loader/loader.conf',
            self._get_template_parameters()
        )

    def set_loader_entry(self, target: str) -> None:
        """
        Setup/update loader entries

        loader entries for systemd-boot are expected to be managed
        through kernel-install. Thus no further action needs to be
        taken by kiwi

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)
        """
        pass

    def _get_template_parameters(self) -> Dict[str, str]:
        return {
            'kernel_file': self.custom_args['kernel'] or 'vmlinuz',
            'initrd_file': self.custom_args['initrd'] or 'initrd',
            'boot_options': self.cmdline,
            'boot_timeout': self.timeout,
            'bootpath': self.get_boot_path(),
            'title': self.get_menu_entry_title()
        }

    @staticmethod
    def _write_config_file(
        template: Template, filename: str, parameters: Dict[str, str]
    ) -> None:
        try:
            config_data = template.substitute(parameters)
            Path.create(os.path.dirname(filename))
            with open(filename, 'w') as config:
                config.write(config_data)
        except Exception as issue:
            raise KiwiTemplateError(
                '{0}: {1}'.format(type(issue).__name__, issue)
            )

    def _write_kernel_cmdline_file(self) -> None:
        kernel_cmdline = f'{self.root_mount.mountpoint}/etc/kernel/cmdline'
        Path.create(os.path.dirname(kernel_cmdline))
        with open(kernel_cmdline, 'w') as cmdline:
            cmdline.write(self.cmdline)
