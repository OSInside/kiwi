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
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.path import Path
from kiwi.command import Command
from kiwi.exceptions import KiwiIsoToolError


class IsoToolsCdrTools(IsoToolsBase):
    """
    Implementation of Parameter API for iso creation tools using
    the cdrkit/cdrtools projects. Addressed here are the option
    compatible tools mkisofs and genisoimage
    """
    def get_tool_name(self):
        """
        There are tools by J.Schilling and tools from the community
        Depending on what is installed a decision needs to be made.
        mkisofs is preferred over genisoimage
        """
        iso_creation_tools = ['mkisofs', 'genisoimage']
        for tool in iso_creation_tools:
            tool_found = Path.which(tool)
            if tool_found:
                return tool_found

        raise KiwiIsoToolError(
            'No iso creation tool found, searched for: %s'.format(
                iso_creation_tools
            )
        )

    def init_iso_creation_parameters(self, sortfile, custom_args=None):
        """
        Create a set of standard parameters

        :param string sortfile: file path name
        :param list custom_args: custom ISO creation args
        """
        if custom_args:
            self.iso_parameters = custom_args
        catalog_file = self.boot_path + '/boot.catalog'
        self.iso_parameters += [
            '-R', '-J', '-f', '-pad', '-joliet-long',
            '-sort', sortfile,
            '-no-emul-boot', '-boot-load-size', '4', '-boot-info-table',
            '-hide', catalog_file,
            '-hide-joliet', catalog_file,
        ]
        loader_file = self.boot_path + '/loader/isolinux.bin'
        self.iso_loaders += [
            '-b', loader_file, '-c', catalog_file
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
        loader_file = self.boot_path + '/efi'
        if os.path.exists(os.sep.join([self.source_dir, loader_file])):
            self.iso_loaders.append('-eltorito-alt-boot')
            iso_tool = self.get_tool_name()
            if iso_tool and CommandCapabilities.has_option_in_help(
                iso_tool, '-eltorito-platform', raise_on_error=False
            ):
                self.iso_loaders += ['-eltorito-platform', 'efi']
            self.iso_loaders += [
                '-b', loader_file, '-no-emul-boot', '-joliet-long'
            ]
            loader_file_512_byte_blocks = os.path.getsize(
                os.sep.join([self.source_dir, loader_file])
            ) / 512
            # boot-load-size is stored in a 16bit range, thus we only
            # set the value if it fits into that range
            if loader_file_512_byte_blocks <= 0xffff:
                self.iso_loaders.append(
                    '-boot-load-size'
                )
                self.iso_loaders.append(
                    format(int(loader_file_512_byte_blocks))
                )

    def create_iso(self, filename, hidden_files=None):
        hidden_files_parameters = []
        if hidden_files:
            for hidden_file in hidden_files:
                hidden_files_parameters.append('-hide')
                hidden_files_parameters.append(hidden_file)
                hidden_files_parameters.append('-hide-joliet')
                hidden_files_parameters.append(hidden_file)
        Command.run(
            [
                self.get_tool_name()
            ] + hidden_files_parameters +
            self.iso_parameters + self.iso_loaders + [
                '-o', filename, self.source_dir
            ]
        )
