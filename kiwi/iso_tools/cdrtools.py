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
import re
from collections import (
    namedtuple,
    OrderedDict
)

# project
from kiwi.utils.temporary import Temporary
from kiwi.defaults import Defaults
from kiwi.iso_tools.base import IsoToolsBase
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.path import Path
from kiwi.command import Command
from kiwi.exceptions import KiwiIsoToolError


class IsoToolsCdrTools(IsoToolsBase):
    """
    **cdrkit/cdrtools wrapper class**

    Implementation of Parameter API for iso creation tools using
    the cdrkit/cdrtools projects. Addressed here are the option
    compatible tools mkisofs and genisoimage
    """
    def has_iso_hybrid_capability(self):
        """
        Indicate if the iso tool has the capability to embed a
        partition table into the iso such that it can be
        used as both; an iso and a disk

        :return: True or False

        :rtype: bool
        """
        return False

    def get_tool_name(self):
        """
        There are tools by J.Schilling and tools from the community
        Depending on what is installed a decision needs to be made.
        mkisofs is preferred over genisoimage

        :raises KiwiIsoToolError: if no iso creation tool is found
        :return: tool name

        :rtype: str
        """
        iso_creation_tools = ['mkisofs', 'genisoimage']
        for tool in iso_creation_tools:
            tool_found = Path.which(tool)
            if tool_found:
                return tool_found

        raise KiwiIsoToolError(
            'No iso creation tool found, searched for: {}'.format(
                iso_creation_tools
            )
        )

    def init_iso_creation_parameters(self, custom_args=None):
        """
        Create a set of standard parameters

        :param list custom_args: custom ISO creation args
        """
        efi_mode = False
        if custom_args:
            if custom_args.get('efi_mode'):
                efi_mode = True
            if 'mbr_id' in custom_args:
                self.iso_parameters += [
                    '-A', custom_args['mbr_id']
                ]
            if 'publisher' in custom_args:
                self.iso_parameters += [
                    '-publisher', custom_args['publisher']
                ]
            if 'preparer' in custom_args:
                self.iso_parameters += [
                    '-p', custom_args['preparer']
                ]
            if 'volume_id' in custom_args:
                self.iso_parameters += [
                    '-V', custom_args['volume_id']
                ]
            if 'udf' in custom_args:
                self.iso_parameters += [
                    '-iso-level', '3', '-udf'
                ]
        catalog_file = self.boot_path + '/boot.catalog'
        self.iso_parameters += [
            '-R', '-J', '-f', '-pad', '-joliet-long',
            '-sort', self._create_sortfile(),
            '-no-emul-boot', '-boot-load-size', '4', '-boot-info-table',
            '-hide', catalog_file,
            '-hide-joliet', catalog_file,
        ]
        if efi_mode:
            loader_file = os.sep.join(
                [
                    self.boot_path, 'loader',
                    Defaults.get_isolinux_bios_grub_loader()
                ]
            )
        else:
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
        """
        Creates the iso file with the given filename using cdrtools

        :param str filename: output filename
        :param list hidden_files: list of hidden files
        """
        hidden_files_parameters = []
        if hidden_files:
            for hidden_file in hidden_files:
                hidden_files_parameters.append('-hide')
                hidden_files_parameters.append(hidden_file)
                hidden_files_parameters.append('-hide-joliet')
                hidden_files_parameters.append(hidden_file)
        iso_parameters = \
            hidden_files_parameters + \
            self.iso_parameters + \
            self.iso_loaders
        Command.run(
            [
                self.get_tool_name()
            ] + iso_parameters + [
                '-o', filename, self.source_dir
            ]
        )

    def list_iso(self, isofile):
        """
        List contents of an ISO image

        :param str isofile: path to the ISO file

        :return: formatted isoinfo result

        :rtype: dict
        """
        listing_type = namedtuple(
            'listing_type', ['name', 'filetype', 'start']
        )
        listing = Command.run(
            [self._get_isoinfo_tool(), '-R', '-l', '-i', isofile]
        )
        listing_result = {}
        for line in listing.output.split(os.linesep):
            iso_entry = re.search(
                '.*(-[-rwx]{9}).*\s\[\s*(\d+)(\s+\d+)?\]\s+(.*?)\s*$', line
            )
            if iso_entry:
                entry_type = iso_entry.group(1)
                entry_name = iso_entry.group(4)
                entry_addr = int(iso_entry.group(2))
                listing_result[entry_addr] = listing_type(
                    name=entry_name,
                    filetype=entry_type,
                    start=entry_addr
                )
        return OrderedDict(
            sorted(listing_result.items())
        )

    def _get_isoinfo_tool(self):
        """
        There are tools by J.Schilling and tools from the community
        This method searches in all paths which could provide an
        isoinfo tool. The first match makes the decision

        :raises KiwiIsoToolError: if no isoinfo tool found
        :return: the isoinfo tool to use

        :rtype: str
        """
        alternative_lookup_paths = ['/usr/lib/genisoimage']
        isoinfo = Path.which('isoinfo', alternative_lookup_paths)
        if isoinfo:
            return isoinfo

        raise KiwiIsoToolError(
            'No isoinfo tool found, searched in PATH: %s and %s' %
            (os.environ.get('PATH'), alternative_lookup_paths)
        )

    def _create_sortfile(self):
        """
        Create isolinux sort file

        :return: iso sort file name

        :rtype: str
        """
        self.iso_sortfile = Temporary().new_file()
        catalog_file = \
            self.source_dir + '/' + self.boot_path + '/boot.catalog'
        loader_file = \
            self.source_dir + '/' + self.boot_path + '/loader/isolinux.bin'
        with open(self.iso_sortfile.name, 'w') as sortfile:
            sortfile.write('%s 3\n' % catalog_file)
            sortfile.write('%s 2\n' % loader_file)

            boot_files = list(os.walk(self.source_dir + '/' + self.boot_path))
            boot_files += list(os.walk(self.source_dir + '/EFI'))
            for basedir, dirnames, filenames in sorted(boot_files):
                for entry in sorted(dirnames + filenames):
                    if entry in filenames and entry == 'efi':
                        sortfile.write('%s/%s 1000001\n' % (basedir, entry))
                    else:
                        sortfile.write('%s/%s 1\n' % (basedir, entry))

            sortfile.write(
                '%s/%s 1000000\n' % (self.source_dir, 'header_end')
            )
        return self.iso_sortfile.name
