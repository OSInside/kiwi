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
from kiwi.defaults import Defaults
from kiwi.command import Command
from kiwi.exceptions import KiwiIsoLoaderError


class Iso:
    """
    **Implements helper methods around the creation of ISO filesystems**
    """
    def __init__(self, source_dir: str) -> None:
        """
        Create an instance of Iso helpers

        :param str source_dir:
            Directory path for iso source dir, root of ISO
        """
        self.source_dir = source_dir
        self.boot_path = Defaults.get_iso_boot_path()

    @staticmethod
    def set_media_tag(isofile: str) -> None:
        """
        Include checksum tag in the ISO so it can be verified with
        the mediacheck program.

        :param str isofile: path to the ISO file
        """
        Command.run(
            [
                'tagmedia',
                '--md5',
                '--check',
                '--pad', '150',
                isofile
            ]
        )

    def setup_isolinux_boot_path(self) -> None:
        """
        Write the base boot path into the isolinux loader binary

        :raises KiwiIsoLoaderError: if loader/isolinux.bin is not found
        """
        loader_base_directory = self.boot_path + '/loader'
        loader_file = '/'.join(
            [self.source_dir, self.boot_path, 'loader/isolinux.bin']
        )
        if not os.path.exists(loader_file):
            raise KiwiIsoLoaderError(
                'No isolinux loader {} found'.format(loader_file)
            )
        try:
            Command.run(
                [
                    'isolinux-config', '--base', loader_base_directory,
                    loader_file
                ]
            )
        except Exception:
            # Setup of the base directory failed. This happens if
            # isolinux-config was not able to identify the isolinux
            # signature. As a workaround a compat directory /isolinux
            # is created which hardlinks all loader files
            loader_source_directory = os.sep.join(
                [self.source_dir, loader_base_directory]
            )
            loader_compat_target_directory = os.sep.join(
                [self.source_dir, 'isolinux']
            )
            Command.run(
                [
                    'cp', '-a', '-l',
                    loader_source_directory + os.sep,
                    loader_compat_target_directory + os.sep
                ]
            )
