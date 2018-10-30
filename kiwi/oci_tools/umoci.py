# Copyright (c) 2018 SUSE Linux GmbH.  All rights reserved.
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
from datetime import datetime

# project
from kiwi.oci_tools.base import OCIBase
from kiwi.command import Command


class OCIUmoci(OCIBase):
    """
    **Open Container Operations using umoci**
    """
    def init_layout(self, base_image=False):
        """
        Initialize a new container layout

        A new container layout can start with a non empty base
        root image. If provided that base layout will be used with
        the given primary tag provided at instance creation time.
        The import and unpack of the base image is not a
        responsibility of this class and done beforehead

        :param string base_image: True|False
        """
        if base_image:
            Command.run(
                [
                    'umoci', 'config', '--image',
                    '{0}:base_layer'.format(self.container_dir),
                    '--tag', self.container_tag
                ]
            )
        else:
            Command.run(
                ['umoci', 'init', '--layout', self.container_dir]
            )
            Command.run(
                ['umoci', 'new', '--image', self.container_name]
            )

    def unpack(self, oci_root_dir):
        """
        Unpack current container root data to given directory

        :param string oci_root_dir: root data directory
        """
        Command.run(
            ['umoci', 'unpack', '--image', self.container_name, oci_root_dir]
        )

    def repack(self, oci_root_dir):
        """
        Pack given root data directory into container image

        :param string oci_root_dir: root data directory
        """
        Command.run(
            ['umoci', 'repack', '--image', self.container_name, oci_root_dir]
        )

    def add_tag(self, tag_name):
        """
        Add additional tag name to the container

        :param string tag_name: A name
        """
        Command.run(
            [
                'umoci', 'config', '--image', self.container_name,
                '--tag', tag_name
            ]
        )

    def set_config(self, oci_config):
        """
        Set list of meta data information such as entry_point,
        maintainer, etc... to the container.

        :param list oci_config: meta data list
        """
        Command.run(
            [
                'umoci', 'config'
            ] + oci_config + [
                '--image', self.container_name,
                '--created', datetime.utcnow().strftime(
                    '%Y-%m-%dT%H:%M:%S+00:00'
                )
            ]
        )

    def garbage_collect(self):
        """
        Cleanup unused data from operations
        """
        Command.run(
            ['umoci', 'gc', '--layout', self.container_dir]
        )
