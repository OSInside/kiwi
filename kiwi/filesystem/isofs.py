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
import logging
from typing import List

# project
from kiwi.filesystem.base import FileSystemBase
from kiwi.iso_tools import IsoTools

log = logging.getLogger('kiwi')


class FileSystemIsoFs(FileSystemBase):
    """
    **Implements creation of iso filesystem**
    """
    def create_on_file(
        self, filename: str, label: str = None, exclude: List[str] = None
    ):
        """
        Create iso filesystem from data tree

        There is no label which could be set for iso filesystem
        thus this parameter is not used

        :param string filename: result file path name
        :param string label: unused
        :param list exclude: unused
        """
        self.filename = filename
        meta_data = self.custom_args['meta_data']
        efi_loader = meta_data.get('efi_loader')
        iso_tool = IsoTools.new(self.root_dir)

        iso_tool.init_iso_creation_parameters(meta_data)

        if efi_loader:
            iso_tool.add_efi_loader_parameters(efi_loader)

        iso_tool.create_iso(self.filename)
