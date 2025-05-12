# Copyright (c) 2025 SUSE LLC.  All rights reserved.
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
from typing import Dict

# project
from kiwi.archive.tar import ArchiveTar
from kiwi.defaults import Defaults
from kiwi.utils.compress import Compress
from kiwi.command import Command
from kiwi.container.base import ContainerImageBase


class ContainerImageWsl(ContainerImageBase):
    """
    Create new WSL root tar
    WSL(Windows Subsystem Linux >= 2.4.4)

    :param string root_dir: root directory path name
    :param dict custom_args:
        Custom processing arguments defined as hash keys
    """
    def __init__(self, root_dir: str, custom_args: Dict[str, str] = {}):
        self.root_dir = root_dir
        self.wsl_config = custom_args or {}

    def create(
        self, filename: str, base_image: str = '',
        ensure_empty_tmpdirs: bool = False, compress_archive: bool = True
    ) -> str:
        """
        Create WSL root tar

        :param string filename: archive file name
        :param string base_image: not-supported
        :param bool ensure_empty_tmpdirs: not-supported
        :param bool compress_archive: not-supported
        """
        exclude_list = Defaults.\
            get_exclude_list_for_root_data_sync() + Defaults.\
            get_exclude_list_from_custom_exclude_files(self.root_dir)
        exclude_list.append('boot')
        exclude_list.append('dev')
        exclude_list.append('sys')
        exclude_list.append('proc')

        archive_file_name = filename
        archive = ArchiveTar(archive_file_name)
        archive_file_name = archive.create(
            self.root_dir, exclude=exclude_list,
            options=['--numeric-owner', '--absolute-names']
        )
        compressor = Compress(archive_file_name)
        archive_file_name = compressor.gzip()

        Command.run(
            ['mv', archive_file_name, filename]
        )
        return filename
