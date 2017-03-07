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
from tempfile import mkdtemp

# project
from kiwi.defaults import Defaults
from kiwi.path import Path
from kiwi.command import Command
from kiwi.utils.sync import DataSync
from kiwi.utils.compress import Compress


class ContainerImageDocker(object):
    """
    Create docker container from a root directory

    Attributes

    * :attr:`root_dir`
        root directory path name

    * :attr:`custom_args`
        representation of the containerconfig and its subsections
    """
    def __init__(self, root_dir, custom_args=None):
        self.root_dir = root_dir
        self.docker_dir = None
        self.docker_root_dir = None

        self.container_name = ''
        self.container_tag = 'latest'
        self.entry_command = []
        self.entry_subcommand = []
        self.maintainer = []
        self.user = []
        self.workingdir = []
        self.expose_ports = []
        self.volumes = []
        self.environment = []
        self.labels = []

        if custom_args:
            if 'container_name' in custom_args:
                self.container_name = custom_args['container_name']

            if 'container_tag' in custom_args:
                self.container_tag = custom_args['container_tag']

            if 'entry_command' in custom_args:
                self.entry_command = custom_args['entry_command']

            if 'entry_subcommand' in custom_args:
                self.entry_subcommand = custom_args['entry_subcommand']

            if 'maintainer' in custom_args:
                self.maintainer = custom_args['maintainer']

            if 'user' in custom_args:
                self.user = custom_args['user']

            if 'workingdir' in custom_args:
                self.workingdir = custom_args['workingdir']

            if 'expose_ports' in custom_args:
                self.expose_ports = custom_args['expose_ports']

            if 'volumes' in custom_args:
                self.volumes = custom_args['volumes']

            if 'environment' in custom_args:
                self.environment = custom_args['environment']

            if 'labels' in custom_args:
                self.labels = custom_args['labels']

        if not self.entry_command and not self.entry_subcommand:
            self.entry_subcommand = ['--config.cmd=/bin/bash']

    def create(self, filename):
        """
        Create compressed docker system container tar archive

        :param string filename: archive file name
        """
        exclude_list = [
            'image', '.profile', '.kconfig', 'boot', 'dev', 'sys', 'proc',
            Defaults.get_shared_cache_location()
        ]

        self.docker_dir = mkdtemp(prefix='kiwi_docker_dir.')
        self.docker_root_dir = mkdtemp(prefix='kiwi_docker_root_dir.')

        container_dir = os.sep.join(
            [self.docker_dir, 'umoci_layout']
        )
        container_name = ':'.join(
            [container_dir, self.container_tag]
        )

        Command.run(
            ['umoci', 'init', '--layout', container_dir]
        )
        Command.run(
            ['umoci', 'new', '--image', container_name]
        )
        Command.run(
            ['umoci', 'unpack', '--image', container_name, self.docker_root_dir]
        )
        docker_root = DataSync(
            ''.join([self.root_dir, os.sep]),
            os.sep.join([self.docker_root_dir, 'rootfs'])
        )
        docker_root.sync_data(
            options=['-a', '-H', '-X', '-A'], exclude=exclude_list
        )
        Command.run(
            ['umoci', 'repack', '--image', container_name, self.docker_root_dir]
        )
        Command.run(
            [
                'umoci', 'config'
            ] +
            self.maintainer +
            self.user +
            self.workingdir +
            self.entry_command +
            self.entry_subcommand +
            self.expose_ports +
            self.volumes +
            self.environment +
            self.labels +
            [
                '--image', container_name,
                '--tag', self.container_tag
            ]
        )
        Command.run(
            ['umoci', 'gc', '--layout', container_dir]
        )

        docker_tarfile = filename.replace('.xz', '')

        # make sure the target tar file does not exist
        # skopeo doesn't support force overwrite
        Path.wipe(docker_tarfile)

        Command.run(
            [
                'skopeo', 'copy', 'oci:{0}'.format(
                    container_name
                ),
                'docker-archive:{0}:{1}:{2}'.format(
                    docker_tarfile, self.container_name, self.container_tag
                )
            ]
        )
        compressor = Compress(docker_tarfile)
        compressor.xz()

    def __del__(self):
        if self.docker_dir:
            Path.wipe(self.docker_dir)
        if self.docker_root_dir:
            Path.wipe(self.docker_root_dir)
