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
import re

# project
from kiwi.bootloader.config.base import BootLoaderConfigBase
from kiwi.bootloader.template.zipl import BootLoaderTemplateZipl
from kiwi.command import Command
from kiwi.logger import log
from kiwi.path import Path
from kiwi.firmware import FirmWare
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiTemplateError,
    KiwiBootLoaderZiplPlatformError,
    KiwiBootLoaderZiplSetupError,
    KiwiDiskGeometryError
)


class BootLoaderConfigZipl(BootLoaderConfigBase):
    """
    **zipl bootloader configuration.**
    """
    def post_init(self, custom_args):
        """
        zipl post initialization method

        :param dict custom_args:
            Contains zipl config arguments

            .. code:: python

                {'targetbase': 'device_name'}
        """
        self.custom_args = custom_args
        arch = platform.machine()
        if 's390' in arch:
            self.arch = arch
        else:
            raise KiwiBootLoaderZiplPlatformError(
                'host architecture %s not supported for zipl setup' % arch
            )

        if not custom_args or 'targetbase' not in custom_args:
            raise KiwiBootLoaderZiplSetupError(
                'targetbase device name is required for zipl setup'
            )

        self.bootpath = '.'
        self.timeout = self.get_boot_timeout_seconds()
        self.cmdline = self.get_boot_cmdline()
        self.cmdline_failsafe = ' '.join(
            [self.cmdline, Defaults.get_failsafe_kernel_options()]
        )
        self.target_blocksize = self.xml_state.build_type.get_target_blocksize()
        if not self.target_blocksize:
            self.target_blocksize = Defaults.get_s390_disk_block_size()

        self.target_type = self.xml_state.build_type.get_zipl_targettype()
        if not self.target_type:
            self.target_type = Defaults.get_s390_disk_type()

        self.failsafe_boot = self.failsafe_boot_entry_requested()
        self.target_device = custom_args['targetbase']
        self.firmware = FirmWare(self.xml_state)
        self.target_table_type = self.firmware.get_partition_table_type()

        self.zipl = BootLoaderTemplateZipl()
        self.config = None

    def write(self):
        """
        Write zipl config file
        """
        log.info('Writing zipl config file')
        config_dir = self._get_zipl_boot_path()
        config_file = config_dir + '/config'
        if self.config:
            Path.create(config_dir)
            with open(config_file, 'w') as config:
                config.write(self.config)

            log.info('Moving initrd/kernel to zipl boot directory')
            Command.run(
                [
                    'mv',
                    self.root_dir + '/boot/initrd.vmx',
                    self.root_dir + '/boot/linux.vmx',
                    self._get_zipl_boot_path()
                ]
            )

    def setup_disk_image_config(
        self, boot_uuid=None, root_uuid=None, hypervisor=None,
        kernel='linux.vmx', initrd='initrd.vmx', boot_options=''
    ):
        """
        Create the zipl config in memory from a template suitable to
        boot from a disk image.

        :param string boot_uuid: unused
        :param string root_uuid: unused
        :param string hypervisor: unused
        :param string kernel: kernel name
        :param string initrd: initrd name
        :param string boot_options: kernel options as string
        """
        log.info('Creating zipl config file from template')
        parameters = {
            'device': self.target_device,
            'target_type': self.target_type,
            'blocksize': self.target_blocksize,
            'offset': self._get_target_offset(),
            'geometry': self._get_target_geometry(),
            'default_boot': '1',
            'bootpath': self.bootpath,
            'boot_timeout': self.timeout,
            'title': self.quote_title(self.get_menu_entry_title()),
            'kernel_file': kernel,
            'initrd_file': initrd,
            'boot_options': ' '.join([self.cmdline, boot_options]),
            'failsafe_boot_options': ' '.join(
                [self.cmdline_failsafe, boot_options]
            )
        }
        log.info('--> Using standard disk boot template')
        template = self.zipl.get_template(self.failsafe_boot)
        try:
            self.config = template.substitute(parameters)
        except Exception as e:
            raise KiwiTemplateError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def setup_disk_boot_images(self, boot_uuid, lookup_path=None):
        """
        On s390 no bootloader images needs to be created

        Thus this method does nothing

        :param string boot_uuid: boot device UUID
        :param string lookup_path: custom module lookup path
        """
        pass

    def _get_zipl_boot_path(self):
        return self.root_dir + '/boot/zipl'

    def _get_target_geometry(self):
        if self.target_table_type == 'dasd':
            return '%d,%d,%d' % (
                self._read_dasd_disk_geometry('cylinders'),
                self._read_dasd_disk_geometry('tracks per cylinder'),
                self._read_dasd_disk_geometry('blocks per track')
            )
        else:
            return '%d,%d,%d' % (
                self._read_msdos_disk_geometry('cylinders'),
                self._read_msdos_disk_geometry('tracks per cylinder'),
                self._read_msdos_disk_geometry('blocks per track')
            )

    def _get_target_offset(self):
        if self.target_table_type == 'dasd':
            blocks = self._read_dasd_disk_geometry('blocks per track')
            bash_command = [
                'fdasd', '-f', '-s', '-p', self.target_device,
                '|', 'head', '-n', '1', '|', 'tr', '-s', '" "'
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
            return start_track * blocks
        else:
            blocks = self._read_msdos_disk_geometry('blocks per track')
            parted_call = Command.run(
                ['parted', '-m', self.target_device, 'unit', 's', 'print']
            )
            parted_output = parted_call.output.lstrip()
            first_partition_format = re.search('1:(.*?)s', parted_output)
            if not first_partition_format:
                raise KiwiDiskGeometryError(
                    'unknown partition format: %s' % parted_output
                )
            start_track = int(first_partition_format.group(1))
            return start_track * blocks

    def _read_msdos_disk_geometry(self, value):
        sfdisk_call = Command.run(
            ['sfdisk', '-g', self.target_device]
        )
        sfdisk_output = sfdisk_call.output.lstrip()
        geometry_format = re.search(
            '/dev.*: (.*) cylinders, (.*) heads, (.*) sectors/track',
            sfdisk_output
        )
        if not geometry_format:
            raise KiwiDiskGeometryError(
                'unknown format for geometry: %s' % sfdisk_output
            )
        result = {
            'cylinders': geometry_format.group(1),
            'tracks per cylinder': geometry_format.group(2),
            'blocks per track': geometry_format.group(3)
        }
        if value in result:
            return int(result[value])

    def _read_dasd_disk_geometry(self, value):
        fdasd = ['fdasd', '-f', '-p', self.target_device]
        bash_command = fdasd + ['|', 'grep', '"' + value + '"']
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
