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
from kiwi.path import Path
from kiwi.utils.sync import DataSync
from kiwi.utils.compress import Compress
from kiwi.command import Command
from kiwi.archive.tar import ArchiveTar
from kiwi.defaults import Defaults


class RootImportDocker(RootImportBase):
    """
    Implements the base class for importing a root system from
    a docker image compressed tarball file.
    """
    def post_init(self):
        """
        Post initialization method
        """
        self.uncompressed_image = None
        self.oci_unpack_dir = None
        self.oci_layout_dir = None

    def sync_data(self):
        """
        Synchronize data from the given base image to the target root
        directory.
        """
        if not self.unknown_uri:
            compressor = Compress(self.image_file)
            compressor.uncompress(True)
            self.uncompressed_image = compressor.uncompressed_filename
            skopeo_uri = 'docker-archive:{0}'.format(self.uncompressed_image)
        else:
            skopeo_uri = self.unknown_uri

        self.oci_layout_dir = mkdtemp(prefix='kiwi_layout_dir.')
        self.oci_unpack_dir = mkdtemp(prefix='kiwi_unpack_dir.')

        Command.run([
            'skopeo', 'copy', skopeo_uri, 'oci:{0}'.format(self.oci_layout_dir)
        ])
        Command.run([
            'umoci', 'unpack', '--image',
            self.oci_layout_dir, self.oci_unpack_dir
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

    def __del__(self):
        if self.oci_layout_dir:
            Path.wipe(self.oci_layout_dir)
        if self.oci_unpack_dir:
            Path.wipe(self.oci_unpack_dir)
        if self.uncompressed_image:
            Path.wipe(self.uncompressed_image)
