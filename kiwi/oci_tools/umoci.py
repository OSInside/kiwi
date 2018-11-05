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
        config_args = self._process_oci_config_to_arguments(oci_config)
        Command.run(
            [
                'umoci', 'config'
            ] + config_args + [
                '--image', self.container_name,
                '--created', datetime.utcnow().strftime(
                    '%Y-%m-%dT%H:%M:%S+00:00'
                )
            ]
        )

    @classmethod                                                # noqa:C091
    def _process_oci_config_to_arguments(self, oci_config):
        """
        Process the oci configuration dictionary into a list of arguments
        for the 'umoci config' command

        :param list oci_config: meta data list

        :return: List of umoci config arguments

        :rtype: list
        """
        arguments = []
        if 'maintainer' in oci_config:
            arguments.append(
                '--author={0}'.format(oci_config['maintainer'])
            )

        if 'user' in oci_config:
            arguments.append(
                '--config.user={0}'.format(oci_config['user'])
            )

        if 'workingdir' in oci_config:
            arguments.append(
                '--config.workingdir={0}'.format(oci_config['workingdir'])
            )

        if 'entry_command' in oci_config:
            if len(oci_config['entry_command']) == 0:
                arguments.append('--clear=config.entrypoint')
            else:
                for arg in oci_config['entry_command']:
                    arguments.append('--config.entrypoint={0}'.format(arg))

        if 'entry_subcommand' in oci_config:
            if len(oci_config['entry_subcommand']) == 0:
                arguments.append('--clear=config.cmd')
            else:
                for arg in oci_config['entry_subcommand']:
                    arguments.append('--config.cmd={0}'.format(arg))

        if 'volumes' in oci_config:
            for vol in oci_config['volumes']:
                arguments.append('--config.volume={0}'.format(vol))

        if 'expose_ports' in oci_config:
            for port in oci_config['expose_ports']:
                arguments.append('--config.exposedports={0}'.format(port))

        if 'environment' in oci_config:
            for name in sorted(oci_config['environment']):
                arguments.append('--config.env={0}={1}'.format(
                    name, oci_config['environment'][name]
                ))

        if 'labels' in oci_config:
            for name in sorted(oci_config['labels']):
                arguments.append('--config.label={0}={1}'.format(
                    name, oci_config['labels'][name]
                ))

        return arguments

    def garbage_collect(self):
        """
        Cleanup unused data from operations
        """
        Command.run(
            ['umoci', 'gc', '--layout', self.container_dir]
        )
