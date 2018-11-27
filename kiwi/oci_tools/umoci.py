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
from tempfile import mkdtemp
import os

# project
from kiwi.oci_tools.base import OCIBase
from kiwi.command import Command
from kiwi.path import Path
from kiwi.utils.command_capabilities import CommandCapabilities


class OCIUmoci(OCIBase):
    """
    **Open Container Operations using umoci**
    """
    def post_init(self):
        """
        Initializes some umoci parameters and options
        """
        self.container_name = ':'.join(
            [self.container_dir, self.container_tag]
        )
        if CommandCapabilities.has_option_in_help(
            'umoci', '--no-history', ['repack', '--help']
        ):
            self.no_history_flag = ['--no-history']
        else:
            self.no_history_flag = []

    def init_layout(self, base_image=False):
        """
        Initialize a new container layout

        A new container layout can start with a non empty base
        root image. If provided that base layout will be used with
        the given primary tag provided at instance creation time.
        The import and unpack of the base image is not a
        responsibility of this class and done beforehead

        :param bool base_image: True|False
        """
        if base_image:
            self.container_name = '{0}:base_layer'.format(self.container_dir)
        else:
            Command.run(
                ['umoci', 'init', '--layout', self.container_dir]
            )
            Command.run(
                ['umoci', 'new', '--image', self.container_name]
            )

    def unpack(self):
        """
        Unpack current container root data
        """
        self.oci_root_dir = mkdtemp(prefix='kiwi_oci_root_dir.')
        Command.run([
            'umoci', 'unpack', '--image',
            self.container_name, self.oci_root_dir
        ])

    def sync_rootfs(self, root_dir, exclude_list=None):
        """
        Synchronizes the image root with the rootfs of the container

        :param string root_dir: root directory of the prepare step
        :param list exclude_list: list of paths to exclude
        """
        self._sync_data(
            ''.join([root_dir, os.sep]),
            os.sep.join([self.oci_root_dir, 'rootfs']),
            exclude_list=exclude_list,
            options=['-a', '-H', '-X', '-A', '--delete']
        )

    def import_rootfs(self, root_dir, exclude_list=None):
        """
        Synchronizes the container rootfs with the root tree of the build

        :param string root_dir: root directory used in prepare step
        :param list exclude_list: list of paths to exclude
        """
        self._sync_data(
            os.sep.join([self.oci_root_dir, 'rootfs', '']),
            root_dir, exclude_list=exclude_list,
            options=['-a', '-H', '-X', '-A']
        )

    def repack(self):
        """
        Pack root data directory into container image
        """
        Command.run(
            ['umoci', 'repack'] + self.no_history_flag + [
                '--image', self.container_name, self.oci_root_dir
            ]
        )

    def add_tag(self, tag_name):
        """
        Add additional tag name to the container

        :param string tag_name: A name
        """
        Command.run(
            ['umoci', 'config'] + self.no_history_flag + [
                '--image', self.container_name, '--tag', tag_name
            ]
        )

    def set_config(self, oci_config, base_image=False):
        """
        Set list of meta data information such as entry_point,
        maintainer, etc... to the container.

        :param list oci_config: meta data list
        :param bool base_image: True|False
        """
        config_args = self._process_oci_config_to_arguments(oci_config)
        Command.run(
            [
                'umoci', 'config'
            ] + config_args + [
                '--history.created', self.creation_date,
                '--image', self.container_name,
                '--tag', self.container_tag,
                '--created', self.creation_date
            ]
        )
        if base_image:
            Command.run(['umoci', 'rm', '--image', self.container_name])
            self.container_name = self.container_name = ':'.join(
                [self.container_dir, self.container_tag]
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

        arguments.extend(self._process_oci_history_to_arguments(oci_config))
        return arguments

    @classmethod
    def _process_oci_history_to_arguments(self, oci_config):
        history_args = []
        if 'history' in oci_config:
            if 'comment' in oci_config['history']:
                history_args.append('--history.comment={0}'.format(
                    oci_config['history']['comment']
                ))
            if 'created_by' in oci_config['history']:
                history_args.append('--history.created_by={0}'.format(
                    oci_config['history']['created_by']
                ))
            if 'author' in oci_config['history']:
                history_args.append('--history.author={0}'.format(
                    oci_config['history']['author']
                ))
        return history_args

    def garbage_collect(self):
        """
        Cleanup unused data from operations
        """
        Command.run(
            ['umoci', 'gc', '--layout', self.container_dir]
        )

    def __del__(self):
        if self.oci_root_dir:
            Path.wipe(self.oci_root_dir)
