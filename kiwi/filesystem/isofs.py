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
# project
from .base import FileSystemBase
from ..command import Command
from ..iso import Iso
from ..path import Path

from ..exceptions import KiwiIsoToolError


class FileSystemIsoFs(FileSystemBase):
    """
    Implements creation of iso filesystem
    """
    def create_on_file(self, filename, label=None, exclude=None):
        """
        Create iso filesystem from data tree

        There is no label which could be set for iso filesystem
        thus this parameter is not used

        :param string filename: result file path name
        :param string label: unused
        :param string exclude: unused
        """
        iso = Iso(self.root_dir)
        iso.init_iso_creation_parameters(
            self.custom_args['create_options']
        )
        iso.add_efi_loader_parameters()
        Command.run(
            [
                self._find_iso_creation_tool()
            ] + iso.get_iso_creation_parameters() + [
                '-o', filename, self.root_dir
            ]
        )
        hybrid_offset = iso.create_header_end_block(filename)
        Command.run(
            [
                self._find_iso_creation_tool(),
                '-hide', iso.header_end_name,
                '-hide-joliet', iso.header_end_name
            ] + iso.get_iso_creation_parameters() + [
                '-o', filename, self.root_dir
            ]
        )
        iso.relocate_boot_catalog(filename)
        iso.fix_boot_catalog(filename)
        return hybrid_offset

    def _find_iso_creation_tool(self):
        """
        There are tools by J.Schilling and tools from the community
        Depending on what is installed a decision needs to be made
        """
        iso_creation_tools = ['mkisofs', 'genisoimage']
        for tool in iso_creation_tools:
            tool_found = Path.which(tool)
            if tool_found:
                return tool_found

        raise KiwiIsoToolError(
            'No iso creation tool found, searched for: %s' %
            iso_creation_tools
        )
