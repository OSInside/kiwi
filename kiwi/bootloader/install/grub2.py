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
import platform

# project
from .base import BootLoaderInstallBase
from ...command import Command
from ...logger import log
from ...defaults import Defaults
from ...mount_manager import MountManager

from ...exceptions import(
    KiwiBootLoaderGrubInstallError,
    KiwiBootLoaderGrubPlatformError
)


class BootLoaderInstallGrub2(BootLoaderInstallBase):
    """
        grub2 bootloader installation
    """
    def post_init(self, custom_args):
        arch = platform.machine()
        self.custom_args = custom_args
        self.firmware = None
        self.efi_mount = None
        self.root_mount = None
        self.boot_mount = None
        self.device_mount = None
        self.proc_mount = None
        self.sysfs_mount = None
        if custom_args and 'firmware' in custom_args:
            self.firmware = custom_args['firmware']

        if self.firmware and 'efi' in self.firmware:
            if not custom_args or 'efi_device' not in custom_args:
                raise KiwiBootLoaderGrubInstallError(
                    'EFI device name required for shim installation'
                )
        if not custom_args or 'boot_device' not in custom_args:
            raise KiwiBootLoaderGrubInstallError(
                'boot device name required for grub2 installation'
            )
        if not custom_args or 'root_device' not in custom_args:
            raise KiwiBootLoaderGrubInstallError(
                'root device name required for grub2 installation'
            )

        if arch == 'x86_64' or arch == 'i686' or arch == 'i586':
            self.target = 'i386-pc'
            self.install_device = self.device
            self.modules = ' '.join(Defaults.get_grub_bios_modules())
            self.install_arguments = ['--skip-fs-probe']
        elif arch.startswith('ppc64'):
            if not custom_args or 'prep_device' not in custom_args:
                raise KiwiBootLoaderGrubInstallError(
                    'prep device name required for grub2 installation on ppc'
                )
            self.target = 'powerpc-ieee1275'
            self.install_device = custom_args['prep_device']
            self.modules = ' '.join(Defaults.get_grub_ofw_modules())
            self.install_arguments = ['--skip-fs-probe', '--no-nvram']
        else:
            raise KiwiBootLoaderGrubPlatformError(
                'host architecture %s not supported for grub2 install' % arch
            )

        self.root_mount = MountManager(
            device=custom_args['root_device']
        )
        self.boot_mount = MountManager(
            device=custom_args['boot_device'],
            mountpoint=self.root_mount.mountpoint + 'boot'
        )
        self.modules_dir = '/usr/lib/grub2/' + self.target

    def install(self):
        """
            install bootloader on disk device
        """
        log.info('Installing grub2 on disk %s', self.device)

        if not self.root_mount.device == self.boot_mount.device:
            self.root_mount.mount()
            self.boot_mount.mount()
            module_directory = self.root_mount.mountpoint \
                + self.modules_dir
            boot_directory = self.boot_mount.mountpoint
        else:
            self.root_mount.mount()
            module_directory = self.root_mount.mountpoint \
                + self.modules_dir
            boot_directory = self.root_mount.mountpoint \
                + '/boot'

        Command.run(
            ['grub2-install'] + self.install_arguments + [
                '--directory', module_directory,
                '--boot-directory', boot_directory,
                '--target', self.target,
                '--modules', self.modules,
                self.install_device
            ]
        )

        if self.firmware == 'uefi':
            self.efi_mount = MountManager(
                device=self.custom_args['efi_device'],
                mountpoint=self.root_mount.mountpoint + '/boot/efi'
            )
            self.device_mount = MountManager(
                device='/dev',
                mountpoint=self.root_mount.mountpoint + '/dev'
            )
            self.proc_mount = MountManager(
                device='/proc',
                mountpoint=self.root_mount.mountpoint + '/proc'
            )
            self.sysfs_mount = MountManager(
                device='/sys',
                mountpoint=self.root_mount.mountpoint + '/sys'
            )
            self.device_mount.bind_mount()
            self.proc_mount.bind_mount()
            self.sysfs_mount.bind_mount()
            self.efi_mount.mount()

            # Before we call shim-install, the grub2-install binary is
            # replaced by a noop. Actually there is no reason for shim-install
            # to call grub2-install because it should only setup the system
            # for EFI secure boot which does not require any bootloader code
            # in the master boot record. In addition kiwi has called
            # grub2-install right before
            Command.run(
                [
                    'cp',
                    self.root_mount.mountpoint + '/usr/sbin/grub2-install',
                    self.root_mount.mountpoint + '/usr/sbin/grub2-install.orig'
                ]
            )
            Command.run(
                [
                    'cp',
                    self.root_mount.mountpoint + '/bin/true',
                    self.root_mount.mountpoint + '/usr/sbin/grub2-install'
                ]
            )
            Command.run(
                [
                    'chroot', self.root_mount.mountpoint,
                    'shim-install', '--removable',
                    self.install_device
                ]
            )
            # restore the grub2-install noop
            Command.run(
                [
                    'cp',
                    self.root_mount.mountpoint + '/usr/sbin/grub2-install.orig',
                    self.root_mount.mountpoint + '/usr/sbin/grub2-install'
                ]
            )

    def __del__(self):
        log.info('Cleaning up %s instance', type(self).__name__)
        if self.device_mount:
            self.device_mount.umount(delete_mountpoint=False)
        if self.proc_mount:
            self.proc_mount.umount(delete_mountpoint=False)
        if self.sysfs_mount:
            self.sysfs_mount.umount(delete_mountpoint=False)
        if self.efi_mount:
            self.efi_mount.umount(delete_mountpoint=False)
        if self.boot_mount:
            self.boot_mount.umount(delete_mountpoint=False)
        if self.root_mount:
            self.root_mount.umount()
