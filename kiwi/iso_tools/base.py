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
import shutil
import logging
from typing import (
    Dict, List, Union
)

# project
from kiwi.defaults import Defaults
from kiwi.command import Command
from kiwi.utils.sync import DataSync
from kiwi.path import Path

log = logging.getLogger('kiwi')


class IsoToolsBase:
    """
    **Base Class for Parameter API for iso creation tools**
    """
    def __init__(self, source_dir: str) -> None:
        """
        Base class for IsoTools

        :param string source_dir: data source dir, usually root_dir
        """
        self.arch = Defaults.get_platform_name()
        self.source_dir = source_dir

        self.boot_path = Defaults.get_iso_boot_path()
        self.iso_parameters: List[str] = []
        self.iso_loaders: List[str] = []

    def get_tool_name(self) -> str:
        """
        Return caller name for iso creation tool

        Implementation in specialized tool class

        :return: tool name

        :rtype: str
        """
        raise NotImplementedError

    def init_iso_creation_parameters(
        self, custom_args: Dict[str, Union[str, bool]] = None
    ) -> None:
        """
        Create a set of standard parameters for the main loader

        Implementation in specialized tool class

        :param list custom_args: unused
        """
        raise NotImplementedError

    def add_efi_loader_parameters(self, loader_file: str) -> None:
        """
        Add ISO creation parameters to embed the EFI loader

        Implementation in specialized tool class
        """
        raise NotImplementedError

    def create_iso(
        self, filename: str, hidden_files: List[str] = None
    ) -> None:
        """
        Create iso file

        Implementation in specialized tool class

        :param str filename: unused
        :param list hidden_files: unused
        """
        raise NotImplementedError

    def list_iso(self, isofile: str) -> None:
        """
        List contents of an ISO image

        :param str isofile: unused
        """
        raise NotImplementedError

    def has_iso_hybrid_capability(self) -> bool:
        """
        Indicate if the iso tool has the capability to embed
        a partition table into the iso such that it can be
        used as both; an iso and a disk

        Implementation in specialized tool class
        """
        raise NotImplementedError

    @staticmethod
    def setup_media_loader_directory(
        lookup_path: str, media_path: str, boot_theme: str
    ):
        loader_data = lookup_path + '/image/loader/'
        media_boot_path = os.sep.join(
            [media_path, Defaults.get_iso_boot_path(), 'loader']
        )
        Path.wipe(loader_data)
        Path.create(loader_data)
        grub_image_file_names = [
            Defaults.get_iso_grub_loader(),
            Defaults.get_iso_grub_mbr()
        ]
        loader_files = []
        for grub_image_file_name in grub_image_file_names:
            grub_file = Defaults.get_grub_path(
                lookup_path, 'i386-pc/{0}'.format(grub_image_file_name),
                raise_on_error=False
            )
            if grub_file and os.path.exists(grub_file):
                loader_files.append(grub_file)

        log.debug('Copying loader files to {0}'.format(loader_data))
        for loader_file in loader_files:
            log.debug('--> Copying {0}'.format(loader_file))
            shutil.copy(loader_file, loader_data)

        bash_command = ' '.join(
            ['cp', lookup_path + '/boot/memtest*', loader_data + '/memtest']
        )
        Command.run(
            command=['bash', '-c', bash_command], raise_on_error=False
        )

        if boot_theme:
            theme_path = ''.join(
                [lookup_path, '/etc/bootsplash/themes/', boot_theme]
            )
            if os.path.exists(theme_path + '/cdrom/gfxboot.cfg'):
                bash_command = ' '.join(
                    ['cp', theme_path + '/cdrom/*', loader_data]
                )
                Command.run(
                    ['bash', '-c', bash_command]
                )
                # don't move down one menu entry the first time a F-key is used
                Command.run(
                    [
                        'gfxboot',
                        '--config-file', loader_data + '/gfxboot.cfg',
                        '--change-config', 'install::autodown=0'
                    ]
                )

            if os.path.exists(theme_path + '/bootloader/message'):
                Command.run(
                    ['cp', theme_path + '/bootloader/message', loader_data]
                )

        Path.create(media_boot_path)
        data = DataSync(
            loader_data, media_boot_path
        )
        data.sync_data(
            options=['-a']
        )
