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
from typing import (
    Dict, List, Optional, Union
)

# project
from kiwi.iso_tools.base import IsoToolsBase
from kiwi.path import Path
from kiwi.command import Command
from kiwi.exceptions import KiwiIsoToolError
from kiwi.defaults import Defaults

log = logging.getLogger('kiwi')


class IsoToolsXorrIso(IsoToolsBase):
    """
    **xorriso wrapper class**

    Implementation of Parameter API for iso creation tools using
    the libburnia project. Addressed here is the tool xorriso
    """
    def has_iso_hybrid_capability(self) -> bool:
        """
        Indicate if the iso tool has the capability to embed a
        partition table into the iso such that it can be
        used as both; an iso and a disk

        :return: True or False

        :rtype: bool
        """
        return True

    def get_tool_name(self) -> str:
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

    def init_iso_creation_parameters(
        self, custom_args: Optional[Dict[str, Union[str, bool]]] = None
    ) -> None:
        """
        Create a set of standard parameters

        :param list custom_args: custom ISO meta data
        """
        legacy_bios_mode = True
        if custom_args:
            application_id = \
                custom_args.get('application_id') or custom_args.get('mbr_id')
            if application_id:
                self.iso_parameters += [
                    '-application_id', format(application_id)
                ]
            if 'publisher' in custom_args:
                self.iso_parameters += [
                    '-publisher', format(custom_args['publisher'])
                ]
            if 'preparer' in custom_args:
                self.iso_parameters += [
                    '-preparer_id', format(custom_args['preparer'])
                ]
            if 'volume_id' in custom_args:
                self.iso_parameters += [
                    '-volid', format(custom_args['volume_id'])
                ]
            if 'legacy_bios_mode' in custom_args:
                legacy_bios_mode = bool(custom_args['legacy_bios_mode'])
        catalog_file = self.boot_path + '/boot.catalog'
        self.iso_parameters += [
            '-joliet', 'on', '-padding', '0'
        ]
        if Defaults.is_ppc64_arch(self.arch):
            self.iso_parameters += [
                '-compliance', 'untranslated_names'
            ]

        if Defaults.is_x86_arch(self.arch) and legacy_bios_mode:
            mbr_file = os.sep.join(
                [
                    self.source_dir, self.boot_path, 'loader',
                    Defaults.get_iso_grub_mbr()
                ]
            )
            loader_file = os.sep.join(
                [
                    self.boot_path, 'loader',
                    Defaults.get_iso_grub_loader()
                ]
            )
            self.iso_loaders += [
                '-boot_image', 'grub', 'bin_path={0}'.format(loader_file)
            ]
            if os.path.exists(mbr_file):
                self.iso_loaders += [
                    '-boot_image', 'grub', 'grub2_mbr={0}'.format(mbr_file)
                ]
            else:
                log.warning(f'No hybrid MBR file found: {mbr_file}: skipped')
            self.iso_loaders += [
                '-boot_image', 'grub', 'grub2_boot_info=on'
            ]

        if Defaults.is_ppc64_arch(self.arch):
            self.iso_loaders += [
                '-boot_image', 'any', 'chrp_boot_part=on'
            ]
        else:
            self.iso_loaders += [
                '-boot_image', 'any', 'partition_offset=16',
                '-boot_image', 'any', 'cat_path={0}'.format(catalog_file),
                '-boot_image', 'any', 'cat_hidden=on',
                '-boot_image', 'any', 'boot_info_table=on',
                '-boot_image', 'any', 'platform_id=0x00',
                '-boot_image', 'any', 'emul_type=no_emulation',
                '-boot_image', 'any', 'load_size=2048'
            ]

    def add_efi_loader_parameters(self, loader_file: str) -> None:
        """
        Add ISO creation parameters to embed the EFI loader

        In order to boot the ISO from EFI, the EFI binary is added as
        alternative loader to the ISO creation parameter list. The
        EFI binary must be included into a fat filesystem in order
        to become recognized by the firmware. For details about this
        file refer to _create_embedded_fat_efi_image() from
        bootloader/config/grub2.py
        """
        self.iso_loaders += [
            '-append_partition', '2', '0xef', loader_file,
            '-boot_image', 'any', 'next',
            '-boot_image', 'any',
            'efi_path=--interval:appended_partition_2:all::',
            '-boot_image', 'any', 'platform_id=0xef',
            '-boot_image', 'any', 'emul_type=no_emulation'
        ]

    def create_iso(
        self, filename: str, hidden_files: List[str] = None
    ) -> None:
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
