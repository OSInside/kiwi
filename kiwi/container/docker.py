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
from kiwi.container.oci import ContainerImageOCI
from kiwi.path import Path
from kiwi.command import Command
from kiwi.utils.compress import Compress


class ContainerImageDocker(ContainerImageOCI):
    """
    **Create docker container from a root directory**
    """
    def pack_image_to_file(self, filename):
        """
        Packs the given oci image into the given filename.

        :param string filename: file name of the resulting packed image
        """
        oci_image = os.sep.join([
            self.oci_dir, ':'.join(['umoci_layout', self.container_tag])
        ])

        additional_tags = []
        for tag in self.additional_tags:
            additional_tags.extend([
                '--additional-tag', '{0}:{1}'.format(self.container_name, tag)
            ])

        # make sure the target tar file does not exist
        # skopeo doesn't support force overwrite
        Path.wipe(filename)
        Command.run(
            [
                'skopeo', 'copy', 'oci:{0}'.format(
                    oci_image
                ),
                'docker-archive:{0}:{1}:{2}'.format(
                    filename, self.container_name, self.container_tag
                )
            ] + additional_tags
        )
        container_compressor = self.runtime_config.get_container_compression()
        if container_compressor:
            compressor = Compress(filename)
            return compressor.xz(self.runtime_config.get_xz_options())
        else:
            return filename
