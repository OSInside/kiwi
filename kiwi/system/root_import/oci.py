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

# project
from kiwi.system.root_import.base import RootImportBase
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
    def post_init(self, custom_args):
        self.archive_transport = custom_args['archive_transport']

    def sync_data(self):
        """
        Synchronize data from the given base image to the target root
        directory.
        """
        if not self.unknown_uri:
            compressor = Compress(self.image_file)
            if compressor.get_format():
                compressor.uncompress(True)
                self.uncompressed_image = compressor.uncompressed_filename
            else:
                self.uncompressed_image = self.image_file
            image_uri = '{0}:{1}'.format(
                self.archive_transport, self.uncompressed_image
            )
        else:
            log.warning('Bypassing base image URI to OCI tools')
            image_uri = self.unknown_uri

        oci = OCI.new()
        oci.import_container_image(image_uri)
        oci.unpack()
        oci.import_rootfs(self.root_dir)

        # A copy of the uncompressed image and its checksum are
        # kept inside the root_dir in order to ensure the later steps
        # i.e. system create are atomic and don't need any third
        # party archive.
        image_copy = Defaults.get_imported_root_image(self.root_dir)
        Path.create(os.path.dirname(image_copy))
        oci.export_container_image(
            image_copy, 'oci-archive', Defaults.get_container_base_image_tag()
        )
        self._make_checksum(image_copy)
