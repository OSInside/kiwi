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
import glob
from string import Template
from contextlib import ExitStack
from typing import Dict

# project
from kiwi.path import Path
from kiwi.bootloader.template.systemd_boot import BootLoaderTemplateSystemdBoot
from kiwi.bootloader.config.bootloader_spec_base import BootLoaderSpecBase
from kiwi.boot.image.base import BootImageBase
from kiwi.mount_manager import MountManager
from kiwi.storage.loop_device import LoopDevice
from kiwi.storage.disk import Disk
from kiwi.command import Command
from kiwi.utils.os_release import OsRelease

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderTargetError,
    KiwiKernelLookupError
)

import kiwi.defaults as defaults


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
        Setup ESP for systemd-boot using bootctl

        For disk images only, setup the ESP layout for systemd boot
        using bootctl. All data will be loaded from the ESP.

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
        self._run_bootctl(self.root_mount.mountpoint)
        self.set_loader_entry(self.root_mount.mountpoint, self.target.disk)

    def set_loader_entry(self, root_dir: str, target: str) -> None:
        """
        Setup/update loader entries

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)
        """
        os_release = OsRelease(root_dir)
        try:
            kernel_name = os.path.basename(
                list(glob.iglob(f'{root_dir}/lib/modules/*'))[0]
            )
        except Exception as issue:
            raise KiwiKernelLookupError(
                f'Kernel lookup in {root_dir}/lib/modules failed with {issue}'
            )
        default_entry = f'{os_release.get("ID")}-{kernel_name}.conf'
        BootLoaderSystemdBoot._write_config_file(
            BootLoaderTemplateSystemdBoot().get_entry_template(),
            root_dir + f'/boot/efi/loader/entries/{default_entry}',
            self._get_template_parameters(default_entry)
        )

    def _create_embedded_fat_efi_image(self, path: str):
        """
        Creates a EFI system partition image at the given path.
        Installs systemd-boot required EFI layout into the image
        """
        fat_image_mbsize = int(
            self.xml_state.build_type
                .get_efifatimagesize() or defaults.EFI_FAT_IMAGE_SIZE
        )
        Command.run(
            ['qemu-img', 'create', path, f'{fat_image_mbsize}M']
        )
        Command.run(
            ['sgdisk', '-n', ':1.0', '-t', '1:EF00', path]
        )
        with LoopDevice(path) as loop_provider:
            loop_provider.create(overwrite=False)
            with Disk('gpt', loop_provider) as disk:
                disk.map_partitions()
                disk.partitioner.partition_id = 1
                disk._add_to_map('efi')
                Command.run(
                    ['mkdosfs', '-n', 'BOOT', disk.partition_map['efi']]
                )
                Path.create(f'{self.root_dir}/boot/efi')
                with ExitStack() as stack:
                    efi_mount = MountManager(
                        device=disk.partition_map['efi'],
                        mountpoint=f'{self.root_dir}/boot/efi'
                    )
                    stack.push(efi_mount)
                    device_mount = MountManager(
                        device='/dev',
                        mountpoint=f'{self.root_dir}/dev'
                    )
                    stack.push(device_mount)
                    proc_mount = MountManager(
                        device='/proc',
                        mountpoint=f'{self.root_dir}/proc'
                    )
                    stack.push(proc_mount)
                    sys_mount = MountManager(
                        device='/sys',
                        mountpoint=f'{self.root_dir}/sys'
                    )
                    stack.push(sys_mount)
                    efi_mount.mount()
                    device_mount.bind_mount()
                    proc_mount.bind_mount()
                    sys_mount.bind_mount()
                    self._run_bootctl(self.root_dir)
                    self.set_loader_entry(self.root_dir, self.target.live)
                Command.run(
                    ['dd', f'if={disk.partition_map["efi"]}', f'of={path}.img']
                )

        Command.run(
            ['mv', f'{path}.img', path]
        )

    def _run_bootctl(self, root_dir: str) -> None:
        """
        Setup ESP for systemd-boot using bootctl
        """
        kernel_info = BootImageBase(
            self.xml_state, root_dir, root_dir
        ).get_boot_names()
        Command.run(
            [
                'chroot', root_dir, 'bootctl', 'install',
                '--esp-path=/boot/efi',
                '--no-variables',
                '--entry-token', 'os-id'
            ]
        )
        Path.wipe(f'{root_dir}/boot/loader')
        self._write_kernel_cmdline_file(root_dir)

        # copy kernel and initrd
        entry_dir = f'{root_dir}/boot/efi/loader/entries'
        os_dir = f'{root_dir}/boot/efi/os'
        Path.create(entry_dir)
        Path.create(os_dir)
        self.custom_args['kernel'] = \
            f'os/{os.path.basename(kernel_info.kernel_filename)}'
        self.custom_args['initrd'] = \
            f'os/{kernel_info.initrd_name}'
        Command.run(
            ['cp', kernel_info.kernel_filename, os_dir]
        )
        Command.run(
            ['cp', f'{root_dir}/boot/{kernel_info.initrd_name}', os_dir]
        )

        # create loader.conf
        BootLoaderSystemdBoot._write_config_file(
            BootLoaderTemplateSystemdBoot().get_loader_template(),
            root_dir + '/boot/efi/loader/loader.conf',
            self._get_template_parameters()
        )

    def _get_template_parameters(
        self, default_entry: str = 'main.conf'
    ) -> Dict[str, str]:
        return {
            'kernel_file': self.custom_args['kernel'] or 'vmlinuz',
            'initrd_file': self.custom_args['initrd'] or 'initrd',
            'boot_options': self.cmdline,
            'boot_timeout': self.timeout,
            'bootpath': self.get_boot_path(),
            'title': self.get_menu_entry_title(),
            'default_entry': default_entry
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

    def _write_kernel_cmdline_file(self, root_dir: str) -> None:
        kernel_cmdline = f'{root_dir}/etc/kernel/cmdline'
        Path.create(os.path.dirname(kernel_cmdline))
        with open(kernel_cmdline, 'w') as cmdline:
            cmdline.write(self.cmdline)
