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
from kiwi.filesystem.base import FileSystemBase
from kiwi.iso_tools.iso import Iso
from kiwi.iso_tools import IsoTools


class FileSystemIsoFs(FileSystemBase):
    """
    **Implements creation of iso filesystem**
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
        meta_data = self.custom_args['meta_data']
        iso_tool = IsoTools(self.root_dir)

        iso = Iso(self.root_dir)
        iso.setup_isolinux_boot_path()

        if not iso_tool.has_iso_hybrid_capability():
            iso.create_header_end_marker()

        iso_tool.init_iso_creation_parameters(meta_data)

        iso_tool.add_efi_loader_parameters()

        iso_tool.create_iso(filename)

        if not iso_tool.has_iso_hybrid_capability():
            hybrid_offset = iso.create_header_end_block(filename)
            iso_tool.create_iso(
                filename, hidden_files=[iso.header_end_name]
            )
            iso.relocate_boot_catalog(filename)
            iso.fix_boot_catalog(filename)
            efi_mode = meta_data['efi_mode'] if 'efi_mode' in meta_data else \
                False
            mbr_id = meta_data['mbr_id'] if 'mbr_id' in meta_data else \
                '0xffffffff'
            iso.create_hybrid(
                hybrid_offset, mbr_id, filename, efi_mode
            )
