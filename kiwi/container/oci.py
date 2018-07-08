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
from kiwi.logger import log
from kiwi.runtime_config import RuntimeConfig


class ContainerImageOCI(object):
    """
    Create oci container from a root directory

    :param string root_dir: root directory path name
    :param dict custom_args:
        Custom processing arguments defined as hash keys:

        Example

        .. code:: python

            {
                'container_name': 'name',
                'container_tag': '1.0',
                'additional_tags': ['current', 'foobar'],
                'entry_command': [
                    '--config.entrypoint=/bin/bash',
                    '--config.entrypoint=-x'
                ],
                'entry_subcommand': [
                    '--config.cmd=ls',
                    '--config.cmd=-l'
                ],
                'maintainer': ['--author=tux'],
                'user': ['--config.user=root'],
                'workingdir': ['--config.workingdir=/root'],
                'expose_ports': [
                    '--config.exposedports=80',
                    '--config.exposedports=42'
                ],
                'volumes': [
                    '--config.volume=/var/log',
                    '--config.volume=/tmp'
                ],
                'environment': ['--config.env=PATH=/bin'],
                'labels': ['--config.label=name=value']
            }
    """
    def __init__(self, root_dir, custom_args=None):         # noqa: C901
        self.root_dir = root_dir
        self.oci_dir = None
        self.oci_root_dir = None

        self.container_name = Defaults.get_default_container_name()
        self.container_tag = Defaults.get_default_container_tag()
        self.additional_tags = []
        self.entry_command = []
        self.entry_subcommand = []
        self.maintainer = []
        self.user = []
        self.workingdir = []
        self.expose_ports = []
        self.volumes = []
        self.environment = []
        self.labels = []

        self.runtime_config = RuntimeConfig()

        if custom_args:
            if 'container_name' in custom_args:
                self.container_name = custom_args['container_name']

            if 'container_tag' in custom_args:
                self.container_tag = custom_args['container_tag']

            if 'additional_tags' in custom_args:
                self.additional_tags = custom_args['additional_tags']

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

        # for builds inside the buildservice we include a reference to the
        # specific build. Thus disturl label only exists inside the
        # buildservice.
        if Defaults.is_buildservice_worker():
            bs_label = 'org.openbuildservice.disturl'
            # Do not label anything if any build service label is
            # already present
            if not [label for label in self.labels if bs_label in label]:
                self._append_buildservice_disturl_label()

        if not custom_args or 'container_name' not in custom_args:
            log.info(
                'No container configuration provided, '
                'using default container name "kiwi-container:latest"'
            )

        if not self.entry_command and not self.entry_subcommand:
            self.entry_subcommand = ['--config.cmd=/bin/bash']

    def create(self, filename, base_image):
        """
        Create compressed oci system container tar archive

        :param string filename: archive file name
        :param string base_image: archive used as a base image
        """
        exclude_list = Defaults.get_exclude_list_for_root_data_sync()
        exclude_list.append('boot')
        exclude_list.append('dev')
        exclude_list.append('sys')
        exclude_list.append('proc')

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
                '{0}:base_layer'.format(container_dir),
                '--tag', self.container_tag
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
        for tag in self.additional_tags:
            Command.run(
                ['umoci', 'config', '--image', container_name, '--tag', tag]
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

        return self.pack_image_to_file(filename)

    def pack_image_to_file(self, filename):
        """
        Packs the oci image into the given filename.

        :param string filename: file name of the resulting packed image
        """
        image_dir = os.sep.join([self.oci_dir, 'umoci_layout'])
        oci_tarfile = ArchiveTar(filename)
        container_compressor = self.runtime_config.get_container_compression()
        if container_compressor:
            return oci_tarfile.create_xz_compressed(
                image_dir, xz_options=self.runtime_config.get_xz_options()
            )
        else:
            return oci_tarfile.create(image_dir)

    def _append_buildservice_disturl_label(self):
        with open(os.sep + Defaults.get_buildservice_env_name()) as env:
            for line in env:
                if line.startswith('BUILD_DISTURL') and '=' in line:
                    disturl = line.split('=')[1].lstrip('\'\"').rstrip('\n\'\"')
                    if disturl:
                        self.labels.append(
                            ''.join([
                                '--config.label=org.openbuildservice.disturl=',
                                disturl
                            ])
                        )
                        return
            log.warning('Could not find BUILD_DISTURL inside .buildenv')

    def __del__(self):
        if self.oci_dir:
            Path.wipe(self.oci_dir)
        if self.oci_root_dir:
            Path.wipe(self.oci_root_dir)
