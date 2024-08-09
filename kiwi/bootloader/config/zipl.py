# Copyright (c) 2024 SUSE Software Solutions Germany GmbH
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
from kiwi.boot.image.base import BootImageBase
from kiwi.bootloader.template.zipl import BootLoaderTemplateZipl
from kiwi.bootloader.config.bootloader_spec_base import BootLoaderSpecBase
from kiwi.command import Command
from kiwi.utils.temporary import Temporary

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderTargetError,
    KiwiDiskGeometryError
)


class BootLoaderZipl(BootLoaderSpecBase):
    def create_loader_image(self, target: str) -> None:
        """
        Nothing to be done here for zipl

        :param str target: unused
        """
        pass  # pragma: nocover

    def setup_loader(self, target: str) -> None:
        """
        Setup temporary zipl config and install zipl for supported targets.
        Please note we are not touching the main zipl.conf file provided
        by the distributors

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)
            Currently only the disk identifier is supported
        """
        if target != self.target.disk:
            raise KiwiBootLoaderTargetError(
                'zipl is only supported with the disk image target'
            )
        boot_path = self.get_boot_path()
        boot_options = self.custom_args['boot_options']
        self._mount_system(
            boot_options.get('root_device'),
            boot_options.get('boot_device'),
            boot_options.get('efi_device'),
            boot_options.get('system_volumes'),
            boot_options.get('system_root_volume')
        )
        root_dir = self.root_mount.mountpoint
        kernel_info = BootImageBase(
            self.xml_state, root_dir, root_dir
        ).get_boot_names()
        self.custom_args['kernel'] = \
            f'{boot_path}/{os.path.basename(kernel_info.kernel_filename)}'
        self.custom_args['initrd'] = \
            f'{boot_path}/{kernel_info.initrd_name}'

        runtime_zipl_config_file = Temporary(
            path=self.root_mount.mountpoint, prefix='kiwi_zipl.conf_'
        ).new_file()

        BootLoaderZipl._write_config_file(
            BootLoaderTemplateZipl().get_loader_template(),
            runtime_zipl_config_file.name,
            self._get_template_parameters()
        )
        self.set_loader_entry(
            self.root_mount.mountpoint, self.target.disk
        )
        self._install_zipl(root_dir, runtime_zipl_config_file.name)

    def set_loader_entry(self, root_dir: str, target: str) -> None:
        """
        Setup/update loader entries of the form
        {boot_path}/loader/entries/{get_entry_name}

        :param str target:
            target identifier, one of disk, live(iso) or install(iso)
        """
        entry_name = self.get_entry_name()
        BootLoaderZipl._write_config_file(
            BootLoaderTemplateZipl().get_entry_template(),
            root_dir + f'{self.entries_dir}/{entry_name}',
            self._get_template_parameters(entry_name)
        )

    def _install_zipl(self, root_dir: str, zipl_config: str) -> None:
        """
        Install zipl on target
        """
        zipl = [
            'chroot', root_dir, 'zipl',
            '--noninteractive',
            '--config', zipl_config.replace(root_dir, ''),
            '--blsdir', self.entries_dir,
            '--verbose'
        ]
        Command.run(zipl)

    def _get_template_parameters(
        self, default_entry: str = ''
    ) -> Dict[str, str]:
        disk_type = self.disk_type or 'SCSI'
        blocksize = self.disk_blocksize or 512
        unsupported_for_target_geometry = ['FBA', 'SCSI']
        targetbase = f'targetbase={self.custom_args.get("targetbase")}'
        geometry = ''
        if disk_type not in unsupported_for_target_geometry:
            geometry = f'targetgeometry={self._get_disk_geometry()}'
        return {
            'kernel_file': self.custom_args['kernel'] or 'vmlinuz',
            'initrd_file': self.custom_args['initrd'] or 'initrd',
            'boot_options': self.cmdline,
            'boot_timeout': self.timeout,
            'bootpath': self.get_boot_path(),
            'targetbase': targetbase,
            'targettype': disk_type,
            'targetblocksize': format(blocksize),
            'targetoffset': self._get_partition_start(),
            'targetgeometry': geometry,
            'title': self.get_menu_entry_title(),
            'default_entry': default_entry
        }

    def _get_disk_geometry(self) -> str:
        target_table_type = self.firmware.get_partition_table_type()
        disk_device = self.custom_args['targetbase']
        disk_geometry = ''
        if target_table_type == 'dasd':
            disk_geometry = '{0},{1},{2}'.format(
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

    def _get_partition_start(self) -> str:
        target_table_type = self.firmware.get_partition_table_type()
        disk_device = self.custom_args['targetbase']
        if target_table_type == 'dasd':
            blocks = self._get_dasd_disk_geometry_element(
                disk_device, 'blocks per track'
            )
            fdasd_command = [
                'fdasd', '-f', '-s', '-p', disk_device,
                '|', 'grep', '"^ "',
                '|', 'head', '-n', '1',
                '|', 'tr', '-s', '" "'
            ]
            fdasd_call = Command.run(
                ['bash', '-c', ' '.join(fdasd_command)]
            )
            fdasd_output = fdasd_call.output
            try:
                start_track = int(fdasd_output.split(' ')[2].lstrip())
            except Exception:
                raise KiwiDiskGeometryError(
                    f'unknown partition format: {fdasd_output}'
                )
            return '{0}'.format(start_track * blocks)
        else:
            sfdisk_command = ' '.join(
                [
                    'sfdisk', '--dump', disk_device,
                    '|', 'grep', '"1 :"',
                    '|', 'cut', '-f1', '-d,',
                    '|', 'cut', '-f2', '-d='
                ]
            )
            return Command.run(
                ['bash', '-c', sfdisk_command]
            ).output.strip()

    def _get_dasd_disk_geometry_element(self, disk_device, search) -> int:
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
                f'unknown format for disk geometry: {fdasd_output}'
            )

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
