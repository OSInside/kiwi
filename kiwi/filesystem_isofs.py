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
from iso import Iso
from command import Command
from filesystem_base import FileSystemBase


class FileSystemIsoFs(FileSystemBase):
    """
        Implements creation of iso filesystem
    """
    def post_init(self, custom_args):
        self.custom_args = custom_args

    def create_on_file(self, filename, label=None):
        # there is no label which could be set for an iso filesystem
        # thus this parameter is not used
        iso = Iso(self.root_dir)
        iso.init_iso_creation_parameters(self.custom_args)
        iso.add_efi_loader_parameters()
        Command.run(
            [
                'genisoimage'
            ] + iso.get_iso_creation_parameters() + [
                '-o', filename, self.root_dir
            ]
        )
        hybrid_offset = iso.create_header_end_block(filename)
        Command.run(
            [
                'genisoimage',
                '-hide', iso.header_end_name,
                '-hide-joliet', iso.header_end_name
            ] + iso.get_iso_creation_parameters() + [
                '-o', filename, self.root_dir
            ]
        )
        return hybrid_offset
