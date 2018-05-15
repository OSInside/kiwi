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
from kiwi.system.root_import.oci import RootImportOCI
from kiwi.logger import log
from kiwi.utils.compress import Compress
from kiwi.command import Command


class RootImportDocker(RootImportOCI):
    """
    Extends OCI import class to hanlde docker images in a xz
    compressed tarball file.
    """
    def extract_oci_image(self):
        """
        Extract and converts to OCI the image from the provided
        image file to a temporary location to KIWI can work with it.
        """
        if not self.unknown_uri:
            compressor = Compress(self.image_file)
            if compressor.get_format():
                compressor.uncompress(True)
                self.uncompressed_image = compressor.uncompressed_filename
            else:
                self.uncompressed_image = self.image_file
            skopeo_uri = 'docker-archive:{0}'.format(self.uncompressed_image)
        else:
            log.warning('Bypassing base image URI to skopeo tool')
            skopeo_uri = self.unknown_uri

        Command.run([
            'skopeo', 'copy', skopeo_uri,
            'oci:{0}:base_layer'.format(self.oci_layout_dir)
        ])
