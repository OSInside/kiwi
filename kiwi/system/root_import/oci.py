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
from tempfile import mkdtemp
import os

# project
from kiwi.system.root_import.base import RootImportBase
from kiwi.logger import log
from kiwi.path import Path
from kiwi.utils.sync import DataSync
from kiwi.command import Command
from kiwi.archive.tar import ArchiveTar
from kiwi.defaults import Defaults


class RootImportOCI(RootImportBase):
    """
    Implements the base class for importing a root system from
    a oci image tarball file.
    """
    def post_init(self, image_uri):
        """
        Post initialization method
        """
        self.uncompressed_image = None
        self.oci_unpack_dir = None
        self.oci_layout_dir = None
        self.tag = image_uri.get_fragment()
        self.oci_layout_dir = mkdtemp(prefix='kiwi_layout_dir.')
        self.oci_unpack_dir = mkdtemp(prefix='kiwi_unpack_dir.')

    def sync_data(self):
        """
        Synchronize data from the given base image to the target root
        directory.
        """
        self.extract_oci_image()
        Command.run([
            'umoci', 'unpack', '--image',
            '{0}:base_layer'.format(self.oci_layout_dir), self.oci_unpack_dir
        ])

        synchronizer = DataSync(
            os.sep.join([self.oci_unpack_dir, 'rootfs', '']),
            ''.join([self.root_dir, os.sep])
        )
        synchronizer.sync_data(options=['-a', '-H', '-X', '-A'])

        # A copy of the uncompressed image and its checksum are
        # kept inside the root_dir in order to ensure the later steps
        # i.e. system create are atomic and don't need any third
        # party archive.
        image_copy = Defaults.get_imported_root_image(self.root_dir)
        Path.create(os.path.dirname(image_copy))
        image_tar = ArchiveTar(image_copy)
        image_tar.create(self.oci_layout_dir)
        self._make_checksum(image_copy)

    def extract_oci_image(self):
        """
        Extract the contents from the provided image file to a temporary
        location KIWI can work with.
        """
        if not self.unknown_uri:
            tar = ArchiveTar(self.image_file)
            self.uncompressed_image = mkdtemp(prefix='kiwi_uncompressed.')
            tar.extract(self.uncompressed_image)
            if self.tag:
                skopeo_uri = 'oci:{0}:{1}'.format(
                    self.uncompressed_image, self.tag
                )
            else:
                skopeo_uri = 'oci:{0}'.format(self.uncompressed_image)
        else:
            log.warning('Bypassing base image URI to skopeo tool')
            skopeo_uri = self.unknown_uri

        Command.run([
            'skopeo', 'copy', skopeo_uri,
            'oci:{0}:base_layer'.format(self.oci_layout_dir)
        ])

    def __del__(self):
        if self.oci_layout_dir:
            Path.wipe(self.oci_layout_dir)
        if self.oci_unpack_dir:
            Path.wipe(self.oci_unpack_dir)
        if (self.uncompressed_image is not None and
                self.uncompressed_image != self.image_file):
            Path.wipe(self.uncompressed_image)
