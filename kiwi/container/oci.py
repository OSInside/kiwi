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
from datetime import datetime

# project
from kiwi.defaults import Defaults
from kiwi.path import Path
from kiwi.command import Command
from kiwi.utils.sync import DataSync
from kiwi.archive.tar import ArchiveTar


class ContainerImageOCI(object):
    """
    Create oci container from a root directory

    Attributes

    * :attr:`root_dir`
        root directory path name

    * :attr:`custom_args`
        Custom processing arguments defined as hash keys:
        * container_name: container name
        * container_tag: container tag name
        * entry_command: container entry command
        * entry_subcommand: container subcommands
        * maintainer: container maintainer
        * user: container user
        * workingdir: container working directory
        * expose_ports: ports to expose from container
        * volumes: storage volumes to attach to container
        * environment: environment variables
        * labels: container labels
        * xz_options: string of XZ compression parameters
    """
    def __init__(self, root_dir, custom_args=None):
        self.root_dir = root_dir
        self.oci_dir = None
        self.oci_root_dir = None

        self.xz_options = None
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

            if 'xz_options' in custom_args:
                self.xz_options = custom_args['xz_options']

        if not self.entry_command and not self.entry_subcommand:
            self.entry_subcommand = ['--config.cmd=/bin/bash']

    def create(self, filename, base_image):
        """
        Create compressed oci system container tar archive

        :param string filename: archive file name

        :param string base_image: archive used as a base image
        """
        exclude_list = [
            'image', '.profile', '.kconfig', 'boot', 'dev', 'sys', 'proc',
            Defaults.get_shared_cache_location()
        ]

        self.oci_dir = mkdtemp(prefix='kiwi_oci_dir.')
        self.oci_root_dir = mkdtemp(prefix='kiwi_oci_root_dir.')

        container_dir = os.sep.join(
            [self.oci_dir, 'umoci_layout']
        )
        container_name = ':'.join(
            [container_dir, self.container_tag]
        )

        if base_image:
            Path.create(container_dir)
            image_tar = ArchiveTar(base_image)
            image_tar.extract(container_dir)
            Command.run([
                'umoci', 'config', '--image',
                container_dir, '--tag', self.container_tag
            ])
        else:
            Command.run(
                ['umoci', 'init', '--layout', container_dir]
            )
            Command.run(
                ['umoci', 'new', '--image', container_name]
            )

        Command.run(
            ['umoci', 'unpack', '--image', container_name, self.oci_root_dir]
        )
        oci_root = DataSync(
            ''.join([self.root_dir, os.sep]),
            os.sep.join([self.oci_root_dir, 'rootfs'])
        )
        oci_root.sync_data(
            options=['-a', '-H', '-X', '-A', '--delete'], exclude=exclude_list
        )
        Command.run(
            ['umoci', 'repack', '--image', container_name, self.oci_root_dir]
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
                '--created', datetime.utcnow().strftime(
                    '%Y-%m-%dT%H:%M:%S+00:00'
                )
            ]
        )
        Command.run(
            ['umoci', 'gc', '--layout', container_dir]
        )

        self.pack_image_to_file(filename)

    def pack_image_to_file(self, filename):
        """
        Packs the oci image into the given filename.

        :param string filename: file name of the resulting packed image
        """
        image_dir = os.sep.join([self.oci_dir, 'umoci_layout'])
        oci_tarfile = ArchiveTar(filename.replace('.xz', ''))
        oci_tarfile.create_xz_compressed(
            image_dir, xz_options=self.xz_options
        )

    def __del__(self):
        if self.oci_dir:
            Path.wipe(self.oci_dir)
        if self.oci_root_dir:
            Path.wipe(self.oci_root_dir)
