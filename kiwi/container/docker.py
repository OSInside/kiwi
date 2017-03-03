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
from ..defaults import Defaults
from ..path import Path
from ..command import Command
from tempfile import mkdtemp
from ..utils.sync import DataSync
from ..utils.compress import Compress


class ContainerImageDocker(object):
    """
    Unpack and create docker containers to and from a root directory

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
        self.uncompressed_image = None

        self.container_name = 'base'
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

        self.docker_dir = mkdtemp(prefix='kiwi_docker_dir.')
        self.docker_root_dir = mkdtemp(prefix='kiwi_docker_root_dir.')
        self.container_dir = os.sep.join(
            [self.docker_dir, 'umoci_layout']
        )
        self.container_dir_name = ':'.join(
            [self.container_dir, self.container_tag]
        )

    def create(self, filename, base_image):
        """
        Create compressed docker system container tar archive

        :param string filename: archive file name
        """
        exclude_list = [
            'image', '.profile', '.kconfig', 'boot', 'dev', 'sys', 'proc',
            Defaults.get_shared_cache_location()
        ]

        if base_image:
            self._unpack_image(base_image)
        else:
            self._init_image()

        docker_root = DataSync(
            ''.join([self.root_dir, os.sep]),
            os.sep.join([self.docker_root_dir, 'rootfs'])
        )
        docker_root.sync_data(
            options=['-a', '-H', '-X', '-A'], exclude=exclude_list
        )
        Command.run([
            'umoci', 'repack', '--image',
            self.container_dir_name, self.docker_root_dir
        ])
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
                '--image', self.container_dir_name,
                '--tag', self.container_tag
            ]
        )
        Command.run(
            ['umoci', 'gc', '--layout', self.container_dir]
        )

        docker_tarfile = filename.replace('.xz', '')

        # make sure the target tar file does not exist
        # skopeo doesn't support force overwrite
        Path.wipe(docker_tarfile)

        Command.run(
            [
                'skopeo', 'copy', 'oci:{0}'.format(
                    self.container_dir_name
                ),
                'docker-archive:{0}:{1}:{2}'.format(
                    docker_tarfile, self.container_name, self.container_tag
                )
            ]
        )
        compressor = Compress(docker_tarfile)
        compressor.xz()

    def unpack_to_root_dir(self, base_image):
        """
        Unpack the base image to the root directory
        """
        self._unpack_image(base_image)
        synchronizer = DataSync(
            os.sep.join([self.docker_root_dir, 'rootfs', '']),
            ''.join([self.root_dir, os.sep])
        )
        synchronizer.sync_data(options=['-a', '-H', '-X', '-A'])

    def _unpack_image(self, base_image):
        if not self.uncompressed_image:
            compressor = Compress(base_image)
            compressor.uncompress(True)
            self.uncompressed_image = compressor.uncompressed_filename
        Command.run([
            'skopeo', 'copy',
            'docker-archive:{0}'.format(self.uncompressed_image),
            'oci:{0}'.format(self.container_dir_name)
        ])
        Command.run([
            'umoci', 'unpack', '--image',
            self.container_dir_name, self.docker_root_dir
        ])

    def _init_image(self):
        Command.run(
            ['umoci', 'init', '--layout', self.container_dir]
        )
        Command.run(
            ['umoci', 'new', '--image', self.container_dir_name]
        )
        Command.run([
            'umoci', 'unpack', '--image',
            self.container_dir_name, self.docker_root_dir
        ])

    def __del__(self):
        if self.docker_dir:
            Path.wipe(self.docker_dir)
        if self.docker_root_dir:
            Path.wipe(self.docker_root_dir)
        if self.uncompressed_image:
            Path.wipe(self.uncompressed_image)
