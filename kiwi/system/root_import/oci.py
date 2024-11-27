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
    Dict, List
)

# project
from kiwi.system.root_import.base import RootImportBase
from kiwi.mount_manager import MountManager
from kiwi.path import Path
from kiwi.defaults import Defaults
from kiwi.utils.compress import Compress
from kiwi.oci_tools import OCI

log = logging.getLogger('kiwi')


class RootImportOCI(RootImportBase):
    """
    Implements the base class for importing a root system from
    a oci image tarball file.
    """
    def post_init(self, custom_args: Dict[str, str]):
        self.archive_transport = custom_args['archive_transport']
        self.compressed_image_files: List[Compress] = []

    def sync_data(self):
        """
        Synchronize data from the given base image to the target root
        directory.
        """
        for image_url in self._get_image_urls():
            with OCI.new() as oci:
                oci.import_container_image(image_url)
                oci.unpack()
                oci.import_rootfs(self.root_dir)

        # A copy of the uncompressed image(all derived imports) and
        # its checksum are kept inside the root_dir in order to ensure
        # the later steps i.e. system create are atomic and don't need
        # any third party archive.
        image_copy = Defaults.get_imported_root_image(self.root_dir)

        Path.create(os.path.dirname(image_copy))
        oci.export_container_image(
            image_copy, 'oci-archive',
            Defaults.get_container_base_image_tag()
        )
        self._make_checksum(image_copy)

    def overlay_data(self) -> None:
        """
        Synchronize data from the given base image to the target root
        directory as an overlayfs mounted target.
        """
        root_dir_ro = f'{self.root_dir}_ro'

        for image_url in self._get_image_urls():
            with OCI.new() as oci:
                oci.import_container_image(image_url)
                oci.unpack()
                oci.import_rootfs(self.root_dir)

        log.debug("renaming %s -> %s", self.root_dir, root_dir_ro)
        pathlib.Path(self.root_dir).replace(root_dir_ro)
        Path.create(self.root_dir)

        self.overlay = MountManager(device='', mountpoint=self.root_dir)
        self.overlay.overlay_mount(root_dir_ro)

    def _get_image_urls(self) -> List[str]:
        if not self.raw_urls:
            image_urls: List[str] = []
            for image_file in self.image_files:
                compressor = Compress(image_file)
                # Increase livetime of the the compressor instances
                # to the livetime of RootImportOCI. They create
                # temporary files which are referenced later and
                # need to live longer than this loop block
                self.compressed_image_files.append(compressor)
                if compressor.get_format():
                    compressor.uncompress(True)
                    uncompressed_image = compressor.uncompressed_filename
                else:
                    uncompressed_image = image_file
                image_urls.append(
                    '{0}:{1}'.format(
                        self.archive_transport, uncompressed_image
                    )
                )
            return image_urls
        else:
            log.warning('Bypassing base image URI to OCI tools')
            return self.raw_urls
