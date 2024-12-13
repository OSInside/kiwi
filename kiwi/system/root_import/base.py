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
import pathlib
from typing import (
    Dict, List, Optional
)

# project
from kiwi.xml_state import XMLState
from kiwi.defaults import Defaults
from kiwi.system.setup import SystemSetup
from kiwi.path import Path
from kiwi.system.uri import Uri
from kiwi.command import Command
from kiwi.mount_manager import MountManager
from kiwi.utils.checksum import Checksum
from kiwi.exceptions import (
    KiwiRootImportError,
    KiwiUriTypeUnknown
)

log = logging.getLogger('kiwi')


class RootImportBase:
    """
    Imports the root system from an already packed image.

    * :attr:`root_dir`
        root directory path name

    * :attr:`image_uris`
        Uri object(s) to store source location(s)

    * :attr:`custom_args`
        Dictonary to set specialized class specific configuration values
    """
    def __init__(
        self, root_dir: str, image_uris: List[Uri],
        custom_args: Dict[str, str] = {}
    ):
        self.raw_urls: List[str] = []
        self.image_files: List[str] = []
        self.overlay: Optional[MountManager] = None
        self.root_dir = root_dir
        for image_uri in image_uris:
            try:
                if image_uri.is_remote():
                    raise KiwiRootImportError(
                        'Only local imports are supported'
                    )

                image_file = image_uri.translate()
                self.image_files.append(image_file)

                if not os.path.exists(image_file):
                    raise KiwiRootImportError(
                        f'Could not stat base image file: {image_file}'
                    )
            except KiwiUriTypeUnknown:
                # Let specialized class handle unknown uri schemes
                raw_url = image_uri.uri
                log.warning(
                    f'Unkown URI type for the base image: {raw_url}'
                )
                self.raw_urls.append(raw_url)

        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Initialization of the specialized import class

        Implementation in specialized root import class
        """
        pass

    def overlay_finalize(self, xml_state: XMLState) -> None:
        """
        Umount the overlay root, delete lower and work directories
        and move the upper (delta) to represent the final root_dir.
        All files that got deleted will be reported in a metadata
        file named Defaults.get_removed_files_name(). This information
        can be used by other tools to know about actively deleted
        files and bring them back at a later point in time.

        :param XMLState xml_state: Instance of XML state
        """
        if self.overlay:
            pinch_reference = f'{self.root_dir}_cow_before_pinch'
            removed = f'{self.root_dir}/{Defaults.get_removed_files_name()}'
            systemfiles = f'{self.root_dir}/{Defaults.get_system_files_name()}'

            system = SystemSetup(xml_state, self.root_dir)

            # Run config-overlay.sh
            system.call_config_overlay_script()

            # Run config-host-overlay.sh
            system.call_config_host_overlay_script(
                working_directory=self.root_dir
            )

            # Include system files if requested
            if xml_state.build_type.get_require_system_files():
                with open(systemfiles, 'a') as systemfiles_fd:
                    # copy on write makes this file to become part of the delta
                    systemfiles_fd.write(os.linesep)
                with open(f'{systemfiles}.libs', 'a') as systemlibs_fd:
                    # copy on write makes this file to become part of the delta
                    systemlibs_fd.write(os.linesep)

            # Umount and rename upper to be the new root
            self.overlay.umount()
            Path.wipe(self.root_dir)
            log.debug("renaming %s -> %s", self.overlay.upper, self.root_dir)
            pathlib.Path(self.overlay.upper).replace(self.root_dir)

            # Create removed files metadata
            if not os.path.isdir(pinch_reference):
                Path.create(pinch_reference)
            exclude_options = []
            removed_files = []
            for item in Defaults.get_exclude_list_for_removed_files_detection():
                exclude_options.append('--exclude')
                exclude_options.append(item)
            get_removed = [
                'rsync', '-av', '--dry-run', '--out-format=%n'
            ] + exclude_options + [
                f'{pinch_reference}/', f'{self.root_dir}/'
            ]
            for item in Command.run(get_removed).output.split(os.linesep):
                entry = f'{pinch_reference}/{item}'
                if item and os.path.exists(entry) and not os.path.isdir(entry):
                    removed_files.append(item)
            Path.wipe(pinch_reference)
            if removed_files:
                with open(removed, 'w') as removed_fd:
                    for filename in removed_files:
                        removed_fd.write(filename)
                        removed_fd.write(os.linesep)

            # delete character device nodes from delta tree.
            # (c) device nodes are used to track deleted files
            # and directories from the lower path of the overlayfs
            # tree. Since we extract the upper path of the overlay
            # any changes to the lower tree cannot be tracked.
            Command.run(
                [
                    'find', self.root_dir, '-type', 'c', '-delete'
                ]
            )
            Path.wipe(self.overlay.lower)
            Path.wipe(self.overlay.work)

    def overlay_data(self):
        """
        Synchronize data from the given base image to the target root
        directory as an overlayfs mounted target.

        Implementation in specialized root import class
        """
        raise NotImplementedError

    def sync_data(self):
        """
        Synchronizes the root system of `image_file` into the root_dir

        Implementation in specialized root import class
        """
        raise NotImplementedError

    def _make_checksum(self, image):
        checksum = Checksum(image)
        checksum.md5(''.join([image, '.md5']))
