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
import logging
from string import Template
from contextlib import ExitStack
from typing import Dict, Tuple

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
from kiwi.utils.sparse import SparseFile

from kiwi.system.kernel import Kernel
from kiwi.exceptions import KiwiTemplateError, KiwiBootLoaderTargetError

import kiwi.defaults as defaults

log = logging.getLogger('kiwi')


class BootLoaderSystemdBoot(BootLoaderSpecBase):
    def post_init(self, custom_args: Dict = {}) -> None:
        """
        Post init for systemd-boot

        In addition to the bootloader spec setup, initialize the
        record of the kernel and initrd files on the ESP

        :param dict custom_args: custom bootloader arguments
        """
        super().post_init(custom_args)
        # kernel and initrd file on the ESP per kernel flavor
        self.boot_files: Dict[str, Tuple[str, str]] = {}

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
            boot_options.get('device_map'),
            boot_options.get('root_device'),
            boot_options.get('boot_device'),
            boot_options.get('efi_device'),
            boot_options.get('system_volumes'),
            boot_options.get('system_root_volume'),
            boot_options.get('system_partitions'),
        )
        dracut_setup = self.xml_state.get_dracut_config('setup')
        self._run_bootctl(self.root_mount.mountpoint)
        if dracut_setup.uefi:
            boot_image = boot_options.get('boot_image')
            if boot_image:
                log.info('Creating UKI EFI binary')
                Command.run(
                    [
                        'mv',
                        boot_image.create_uki(self.cmdline),
                        f'{self.root_mount.mountpoint}/boot/efi/EFI/Linux/',
                    ]
                )
        else:
            log.info('Creating loader entry')
            self.set_loader_entry(self.root_mount.mountpoint, self.target.disk)

    def set_loader_entry(self, root_dir: str, target: str) -> None:
        """
        Setup/update loader entries, one entry for the kernel of
        each kernel flavor, see get_kernel_flavors()

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)
        """
        for flavor in self.get_kernel_flavors():
            entry_name = self._get_entry_name(root_dir, flavor)
            BootLoaderSystemdBoot._write_config_file(
                BootLoaderTemplateSystemdBoot().get_entry_template(),
                root_dir + f'/boot/efi/loader/entries/{entry_name}',
                self._get_template_parameters(entry_name, flavor),
            )

    def _create_embedded_fat_efi_image(self, path: str):
        """
        Creates a EFI system partition image at the given path.
        Installs systemd-boot required EFI layout into the image
        """
        fat_image_mbsize = int(
            self.xml_state.build_type.get_efifatimagesize()
            or defaults.EFI_FAT_IMAGE_SIZE
        )
        SparseFile.create(path, f'{fat_image_mbsize}M')
        Command.run(['sgdisk', '-n', ':1.0', '-t', '1:EF00', path])
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
                        mountpoint=f'{self.root_dir}/boot/efi',
                    )
                    stack.push(efi_mount)
                    device_mount = MountManager(
                        device='/dev', mountpoint=f'{self.root_dir}/dev'
                    )
                    stack.push(device_mount)
                    proc_mount = MountManager(
                        device='/proc', mountpoint=f'{self.root_dir}/proc'
                    )
                    stack.push(proc_mount)
                    sys_mount = MountManager(
                        device='/sys', mountpoint=f'{self.root_dir}/sys'
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

        Command.run(['mv', f'{path}.img', path])

    def _run_bootctl(self, root_dir: str) -> None:
        """
        Setup ESP for systemd-boot using bootctl
        """
        Command.run(
            [
                'chroot',
                root_dir,
                'bootctl',
                'install',
                '--esp-path=/boot/efi',
                '--no-variables',
                '--entry-token',
                'os-id',
            ]
        )
        self._write_kernel_cmdline_file(root_dir)

        # copy kernel and initrd of each kernel flavor
        dracut_setup = self.xml_state.get_dracut_config('setup')
        if not dracut_setup.uefi:
            entry_dir = f'{root_dir}/boot/efi/loader/entries'
            os_dir = f'{root_dir}/boot/efi/os'
            Path.create(entry_dir)
            Path.create(os_dir)
            for flavor in self.get_kernel_flavors():
                kernel_info = BootImageBase(
                    self.xml_state, root_dir, root_dir
                ).get_boot_names(flavor)
                self.boot_files[flavor] = (
                    f'os/{os.path.basename(kernel_info.kernel_filename)}',
                    f'os/{kernel_info.initrd_name}',
                )
                Command.run(['cp', kernel_info.kernel_filename, os_dir])
                Command.run(
                    ['cp', f'{root_dir}/boot/{kernel_info.initrd_name}', os_dir]
                )

        # create loader.conf, the entry of the first kernel flavor
        # is the default entry
        kernel_flavors = (
            self.xml_state.get_build_type_bootloader_kernel_flavors()
        )
        default_entry = 'main.conf'
        if kernel_flavors:
            default_entry = self._get_entry_name(root_dir, kernel_flavors[0])
        BootLoaderSystemdBoot._write_config_file(
            BootLoaderTemplateSystemdBoot().get_loader_template(
                with_default_entry=bool(kernel_flavors)
            ),
            root_dir + '/boot/efi/loader/loader.conf',
            self._get_template_parameters(default_entry),
        )

    def _get_entry_name(self, root_dir: str, flavor: str = '') -> str:
        """
        Name of the loader entry of the kernel of the given flavor

        The entry belongs to the kernel of the latest version of the
        flavor, the one kiwi creates the initrd for

        :param str root_dir: path to root directory tree
        :param str flavor: kernel flavor, see Kernel.get_kernel()

        :return: entry file basename

        :rtype: str
        """
        os_release = OsRelease(root_dir)
        kernel_info = Kernel(root_dir).get_kernel(
            raise_on_not_found=True, flavor=flavor
        )
        kernel_name = kernel_info.version if kernel_info else ''
        return f'{os_release.get("ID")}-{kernel_name}.conf'

    def _get_template_parameters(
        self, default_entry: str = 'main.conf', flavor: str = ''
    ) -> Dict[str, str]:
        kernel_file, initrd_file = self.boot_files.get(
            flavor, (self.custom_args['kernel'], self.custom_args['initrd'])
        )
        return {
            'kernel_file': kernel_file or 'vmlinuz',
            'initrd_file': initrd_file or 'initrd',
            'boot_options': self.cmdline,
            'boot_timeout': self.timeout,
            'bootpath': self.get_boot_path(),
            'title': self.get_kernel_flavor_title(
                self.get_menu_entry_title(), flavor
            ),
            'default_entry': default_entry,
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
