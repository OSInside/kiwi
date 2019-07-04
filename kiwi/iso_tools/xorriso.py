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

# project
from kiwi.iso_tools.base import IsoToolsBase
from kiwi.path import Path
from kiwi.command import Command
from kiwi.exceptions import KiwiIsoToolError
from kiwi.defaults import Defaults


class IsoToolsXorrIso(IsoToolsBase):
    """
    **xorriso wrapper class**

    Implementation of Parameter API for iso creation tools using
    the libburnia project. Addressed here is the tool xorriso
    """
    def has_iso_hybrid_capability(self):
        """
        Indicate if the iso tool has the capability to embed a
        partition table into the iso such that it can be
        used as both; an iso and a disk

        :return: True or False

        :rtype: bool
        """
        return True

    def get_tool_name(self):
        """
        Lookup xorriso in search path

        :raises KiwiIsoToolError: if xorriso tool is not found
        :return: xorriso tool path

        :rtype: str
        """
        xorriso = Path.which('xorriso')
        if xorriso:
            return xorriso

        raise KiwiIsoToolError('xorriso tool not found')

    def init_iso_creation_parameters(self, custom_args=None):
        """
        Create a set of standard parameters

        :param list custom_args: custom ISO meta data
        """
        efi_mode = False
        if custom_args:
            if custom_args.get('efi_mode'):
                efi_mode = True
            if 'mbr_id' in custom_args:
                self.iso_parameters += [
                    '-application_id', custom_args['mbr_id']
                ]
            if 'publisher' in custom_args:
                self.iso_parameters += [
                    '-publisher', custom_args['publisher']
                ]
            if 'preparer' in custom_args:
                self.iso_parameters += [
                    '-preparer_id', custom_args['preparer']
                ]
            if 'volume_id' in custom_args:
                self.iso_parameters += [
                    '-volid', custom_args['volume_id']
                ]
        catalog_file = self.boot_path + '/boot.catalog'
        self.iso_parameters += [
            '-joliet', 'on', '-padding', '0'
        ]

        if Defaults.is_x86_arch(self.arch):
            if efi_mode:
                loader_file = os.sep.join(
                    [
                        self.boot_path, 'loader',
                        Defaults.get_isolinux_bios_grub_loader()
                    ]
                )
                mbr_file = os.sep.join(
                    [self.source_dir, self.boot_path, '/loader/boot_hybrid.img']
                )
                self.iso_loaders += [
                    '-boot_image', 'grub', 'bin_path={0}'.format(loader_file),
                    '-boot_image', 'grub', 'grub2_mbr={0}'.format(mbr_file),
                    '-boot_image', 'grub', 'grub2_boot_info=on'
                ]
            else:
                loader_file = self.boot_path + '/loader/isolinux.bin'
                mbr_file = Path.which(
                    'isohdpfx.bin', Defaults.get_syslinux_search_paths()
                )
                self.iso_loaders += [
                    '-boot_image', 'isolinux', 'bin_path={0}'.format(
                        loader_file
                    ),
                    '-boot_image', 'isolinux', 'system_area={0}'.format(
                        mbr_file
                    ),
                    '-boot_image', 'isolinux', 'partition_table=on',
                ]

        self.iso_loaders += [
            '-boot_image', 'any', 'partition_offset=16',
            '-boot_image', 'any', 'cat_path={0}'.format(catalog_file),
            '-boot_image', 'any', 'cat_hidden=on',
            '-boot_image', 'any', 'boot_info_table=on',
            '-boot_image', 'any', 'platform_id=0x00',
            '-boot_image', 'any', 'emul_type=no_emulation',
            '-boot_image', 'any', 'load_size=2048'
        ]

    def add_efi_loader_parameters(self):
        """
        Add ISO creation parameters to embed the EFI loader

        In order to boot the ISO from EFI, the EFI binary is added as
        alternative loader to the ISO creation parameter list. The
        EFI binary must be included into a fat filesystem in order
        to become recognized by the firmware. For details about this
        file refer to _create_embedded_fat_efi_image() from
        bootloader/config/grub2.py
        """
        loader_file = os.sep.join([self.source_dir, self.boot_path, 'efi'])
        if os.path.exists(loader_file):
            self.iso_loaders += [
                '-append_partition', '2', '0xef', loader_file,
                '-boot_image', 'any', 'next',
                '-boot_image', 'any',
                'efi_path=--interval:appended_partition_2:all::',
                '-boot_image', 'any', 'platform_id=0xef',
                '-boot_image', 'any', 'emul_type=no_emulation'
            ]

    def create_iso(self, filename, hidden_files=None):
        """
        Creates the iso file with the given filename using xorriso

        :param str filename: output filename
        :param list hidden_files: list of hidden files
        """
        hidden_files_parameters = []
        if hidden_files:
            for hidden_file in hidden_files:
                hidden_files_parameters += [
                    '--', '-find', hidden_file, '-exec', 'hide', 'on'
                ]
        Path.wipe(filename)
        Command.run(
            [
                self.get_tool_name()
            ] + self.iso_parameters + [
                '-outdev', filename, '-map', self.source_dir, '/',
                '-chmod', '0755', '/', '--'
            ] + self.iso_loaders + hidden_files_parameters
        )
