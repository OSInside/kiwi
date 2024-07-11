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
import glob
import os
import re
import logging
from contextlib import ExitStack

# project
from kiwi.bootloader.install.base import BootLoaderInstallBase
from kiwi.command import Command
from kiwi.defaults import Defaults
from kiwi.mount_manager import MountManager
from kiwi.system.setup import SystemSetup
from kiwi.path import Path

from kiwi.exceptions import (
    KiwiBootLoaderGrubInstallError,
    KiwiBootLoaderGrubPlatformError,
    KiwiBootLoaderGrubDataError,
    KiwiBootLoaderDiskPasswordError
)

log = logging.getLogger('kiwi')


class BootLoaderInstallGrub2(BootLoaderInstallBase):
    """
    **grub2 bootloader installation**
    """
    def post_init(self, custom_args):
        """
        grub2 post initialization method

        :param dict custom_args:
            Contains custom grub2 bootloader arguments

            .. code:: python

                {
                    'target_removable': bool,
                    'system_volumes': list_of_volumes,
                    'system_root_volume': root volume name if required
                    'firmware': FirmWare_instance,
                    'efi_device': string,
                    'boot_device': string,
                    'root_device': string
                }

        """
        self.arch = Defaults.get_platform_name()
        self.custom_args = custom_args
        self.install_arguments = []
        self.shim_install_arguments = []
        self.firmware = None
        self.root_mount = None
        self.volumes = None
        self.root_volume_name = None
        self.target_removable = None
        if custom_args and 'target_removable' in custom_args:
            self.target_removable = custom_args['target_removable']
        if custom_args and 'system_volumes' in custom_args:
            self.volumes = custom_args['system_volumes']
        if custom_args and 'system_root_volume' in custom_args:
            self.root_volume_name = custom_args['system_root_volume']
        if custom_args and 'firmware' in custom_args:
            self.firmware = custom_args['firmware']
        if custom_args and 'install_options' in custom_args:
            self.install_arguments = custom_args['install_options']
        if custom_args and 'shim_options' in custom_args:
            self.shim_install_arguments = custom_args['shim_options']

        if self.firmware and self.firmware.efi_mode():
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

    def install_required(self):
        """
        Check if grub2 has to be installed

        Take architecture and firmware setup into account to check if
        bootloader code in a boot record is required

        :return: True or False

        :rtype: bool
        """
        if 'ppc64' in self.arch and self.firmware.opal_mode():
            # OPAL doesn't need a grub2 stage1, just a config file.
            # The machine will be setup to kexec grub2 in user space
            log.info(
                'No grub boot code installation in opal mode on %s', self.arch
            )
            return False
        elif 'arm' in self.arch or self.arch == 'aarch64':
            # On arm grub2 is used for EFI setup only, no install
            # of grub2 boot code makes sense
            log.info(
                'No grub boot code installation on %s', self.arch
            )
            return False
        elif self.arch == 'riscv64':
            # On riscv grub2 is used for EFI setup only, no install
            # of grub2 boot code makes sense
            log.info(
                'No grub boot code installation on %s', self.arch
            )
            return False
        elif self.firmware.efi_mode() and not self.firmware.legacy_bios_mode():
            # In EFI mode without CSM, no install
            # of grub2 boot code makes sense
            log.info(
                'No grub boot code installation in EFI only mode'
            )
            return False
        return True

    def install(self):
        """
        Install bootloader on disk device
        """
        log.info('Installing grub2 on disk %s', self.device)

        if self.target_removable:
            self.install_arguments.append('--removable')

        if Defaults.is_x86_arch(self.arch):
            self.target = 'i386-pc'
            self.install_device = self.device
            self.modules = ' '.join(
                Defaults.get_grub_bios_modules(multiboot=True)
            )
            self.install_arguments.append('--skip-fs-probe')
        elif self.arch.startswith('ppc64'):
            if not self.custom_args or 'prep_device' not in self.custom_args:
                raise KiwiBootLoaderGrubInstallError(
                    'prep device name required for grub2 installation on ppc'
                )
            self.target = 'powerpc-ieee1275'
            self.install_device = self.custom_args['prep_device']
            self.modules = ' '.join(Defaults.get_grub_ofw_modules())
            self.install_arguments.append('--skip-fs-probe')
            self.install_arguments.append('--no-nvram')
        elif self.arch.startswith('s390'):
            self.target = 's390x-emu'
            self.install_device = self.device
            self.modules = ' '.join(Defaults.get_grub_s390_modules())
            self.install_arguments.append('--skip-fs-probe')
            self.install_arguments.append('--no-nvram')
        else:
            raise KiwiBootLoaderGrubPlatformError(
                'host architecture %s not supported for grub2 installation' %
                self.arch
            )

        with ExitStack() as stack:
            self._mount_device_and_volumes(stack)

            # check if a grub installation could be found in the image system
            module_directory = Defaults.get_grub_path(
                self.root_mount.mountpoint, self.target, raise_on_error=False
            )
            if not module_directory:
                raise KiwiBootLoaderGrubDataError(
                    'No grub2 installation found in {0} for target {1}'.format(
                        self.root_mount.mountpoint, self.target
                    )
                )
            module_directory = module_directory.replace(
                self.root_mount.mountpoint, ''
            )
            boot_directory = '/boot'

            # wipe existing grubenv to allow the grub installer
            # to create a new one
            grubenv_glob = os.sep.join(
                [self.root_mount.mountpoint, 'boot', '*', 'grubenv']
            )
            for grubenv in glob.glob(grubenv_glob):
                Path.wipe(grubenv)

            # install grub2 boot code
            if self.firmware.get_partition_table_type() == 'dasd':
                # On s390 and in CDL mode (4k DASD) the call of grub2-install
                # does not work because grub2-install is not able to identify
                # a 4k fdasd partitioned device as a grub supported device
                # and fails. As grub2-install is only used to invoke
                # grub2-zipl-setup and has no other job to do we can
                # circumvent this problem by directly calling grub2-zipl-setup
                # instead.
                Command.run(
                    [
                        'chroot', self.root_mount.mountpoint,
                        'grub2-zipl-setup', '--keep'
                    ]
                )
            else:
                Command.run(
                    [
                        'chroot', self.root_mount.mountpoint,
                        self._get_grub2_install_tool_name(
                            self.root_mount.mountpoint
                        )
                    ] + self.install_arguments + [
                        '--directory', module_directory,
                        '--boot-directory', boot_directory,
                        '--target', self.target,
                        '--modules', self.modules,
                        self.install_device
                    ]
                )
            # Cleanup temporary modified zipl template and config files
            # back to its original state or lave a .kiwi copy for
            # reference in the system
            zipl_config_file = ''.join(
                [
                    self.root_mount.mountpoint, '/boot/zipl/config'
                ]
            )
            zipl2grub_config_file_orig = ''.join(
                [
                    self.root_mount.mountpoint,
                    '/etc/default/zipl2grub.conf.in.orig'
                ]
            )
            if os.path.exists(zipl2grub_config_file_orig):
                Command.run(
                    [
                        'mv', zipl2grub_config_file_orig,
                        zipl2grub_config_file_orig.replace('.orig', '')
                    ]
                )
            if os.path.exists(zipl_config_file):
                Command.run(
                    ['mv', zipl_config_file, zipl_config_file + '.kiwi']
                )

            # Rebuild security context
            setup = SystemSetup(self.xml_state, self.root_mount.mountpoint)
            setup.setup_selinux_file_contexts()

    def secure_boot_install(self):
        if self.firmware and self.firmware.efi_mode() == 'uefi' and (
            Defaults.is_x86_arch(self.arch)
            or 'arm' in self.arch or self.arch == 'aarch64'     # noqa: W503
        ):
            with ExitStack() as stack:
                self._mount_device_and_volumes(stack)
                shim_install = self._get_shim_install_tool_name(
                    self.root_mount.mountpoint
                )
                # if shim-install does _not_ exist the fallback mechanism
                # has applied at the bootloader/config level and we expect
                # no further tool calls to be required
                if shim_install:
                    # Before we call shim-install, the grub installer binary is
                    # replaced by a noop. Actually there is no reason for
                    # shim-install to call the grub installer because it should
                    # only setup the system for EFI secure boot which does not
                    # require any bootloader code in the master boot record.
                    # In addition kiwi has called the grub installer right
                    # before
                    try:
                        self._disable_grub2_install(self.root_mount.mountpoint)
                        Command.run(
                            [
                                'chroot', self.root_mount.mountpoint,
                                'shim-install', '--removable'
                            ] + self.shim_install_arguments + [
                                self.device
                            ]
                        )
                    finally:
                        # restore the grub installer noop
                        self._enable_grub2_install(self.root_mount.mountpoint)

    def set_disk_password(self, password: str):
        with ExitStack() as stack:
            self._mount_device_and_volumes(stack)
            if self.root_mount and password is not None:
                log.debug('Include cryptomount credentials...')
                config_file = f'{self.root_mount.mountpoint}/boot/efi/EFI/BOOT/grub.cfg'
                try:
                    with open(config_file) as config:
                        grub_config = config.read()
                        grub_config = re.sub(
                            r'cryptomount',
                            f'cryptomount -p "{password}"',
                            grub_config
                        )
                    with open(config_file, 'w') as grub_config_file:
                        grub_config_file.write(grub_config)
                        log.debug(f'<<< {grub_config} >>>')
                except IOError as issue:
                    raise KiwiBootLoaderDiskPasswordError(
                        f'Failed to open {config_file}: {issue}'
                    )

    def _mount_device_and_volumes(self, stack: ExitStack):
        self.root_mount = MountManager(
            device=self.custom_args['root_device']
        )
        stack.push(self.root_mount)
        custom_root_mount_args = []
        if self.root_volume_name and self.root_volume_name != '/':
            custom_root_mount_args += [f'subvol={self.root_volume_name}']
        self.root_mount.mount(options=custom_root_mount_args)

        if 's390' in self.arch:
            boot_mount = MountManager(
                device=self.custom_args['boot_device'],
                mountpoint=self.root_mount.mountpoint + '/boot/zipl'
            )
        else:
            boot_mount = MountManager(
                device=self.custom_args['boot_device'],
                mountpoint=self.root_mount.mountpoint + '/boot'
            )
        stack.push(boot_mount)
        if not self.root_mount.device == boot_mount.device:
            boot_mount.mount()

        if self.custom_args.get('efi_device'):
            efi_mount = MountManager(
                device=self.custom_args['efi_device'],
                mountpoint=self.root_mount.mountpoint + '/boot/efi'
            )
            stack.push(efi_mount)
            efi_mount.mount()

        if self.volumes:
            for volume_path in Path.sort_by_hierarchy(
                sorted(self.volumes.keys())
            ):
                volume_mount = MountManager(
                    device=self.volumes[volume_path]['volume_device'],
                    mountpoint=self.root_mount.mountpoint + '/' + volume_path
                )
                stack.push(volume_mount)
                volume_mount.mount(
                    options=[self.volumes[volume_path]['volume_options']]
                )
        device_mount = MountManager(
            device='/dev',
            mountpoint=self.root_mount.mountpoint + '/dev'
        )
        stack.push(device_mount)
        device_mount.bind_mount()

        proc_mount = MountManager(
            device='/proc',
            mountpoint=self.root_mount.mountpoint + '/proc'
        )
        stack.push(proc_mount)
        proc_mount.bind_mount()

        sysfs_mount = MountManager(
            device='/sys',
            mountpoint=self.root_mount.mountpoint + '/sys'
        )
        stack.push(sysfs_mount)
        sysfs_mount.bind_mount()

    def _disable_grub2_install(self, root_path):
        if os.access(root_path, os.W_OK):
            grub2_install = ''.join(
                [
                    '/usr/sbin/',
                    self._get_grub2_install_tool_name(root_path)
                ]
            )
            grub2_install_backup = ''.join(
                [grub2_install, '.orig']
            )
            grub2_install_noop = '/bin/true'
            Command.run(
                [
                    'chroot', root_path,
                    'cp', '-p', grub2_install, grub2_install_backup
                ]
            )
            Command.run(
                [
                    'chroot', root_path,
                    'cp', grub2_install_noop, grub2_install
                ]
            )

    def _enable_grub2_install(self, root_path):
        if os.access(root_path, os.W_OK):
            grub2_install = ''.join(
                [
                    '/usr/sbin/',
                    self._get_grub2_install_tool_name(root_path)
                ]
            )
            grub2_install_backup = ''.join(
                [grub2_install, '.orig']
            )
            if os.path.exists(''.join([root_path, grub2_install_backup])):
                Command.run(
                    [
                        'chroot', root_path,
                        'mv', grub2_install_backup, grub2_install
                    ]
                )

    def _get_grub2_install_tool_name(self, root_path):
        return self._get_tool_name(
            root_path, lookup_list=['grub2-install', 'grub-install']
        )

    def _get_shim_install_tool_name(self, root_path):
        return self._get_tool_name(
            root_path, lookup_list=['shim-install'], fallback_on_not_found=False
        )

    def _get_tool_name(
        self, root_path, lookup_list, fallback_on_not_found=True
    ):
        for tool in lookup_list:
            if Path.which(filename=tool, root_dir=root_path):
                return tool

        if fallback_on_not_found:
            # no tool from the list was found, we intentionally don't
            # raise here but return the default tool name and raise
            # an exception at invocation time in order to log the
            # expected call and its arguments
            return lookup_list[0]
