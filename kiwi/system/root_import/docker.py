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
        compressor = Compress(self.image_file)
        compressor.uncompress(True)
        self.uncompressed_image = compressor.uncompressed_filename

        self.oci_layout_dir = mkdtemp(prefix='kiwi_layout_dir.')
        self.oci_unpack_dir = mkdtemp(prefix='kiwi_unpack_dir.')

        Command.run([
            'skopeo', 'copy',
            'docker-archive:{0}'.format(self.uncompressed_image),
            'oci:{0}'.format(self.oci_layout_dir)
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

    def __del__(self):
        if self.oci_layout_dir:
            Path.wipe(self.oci_layout_dir)
        if self.oci_unpack_dir:
            Path.wipe(self.oci_unpack_dir)
        if self.uncompressed_image:
            Path.wipe(self.uncompressed_image)
