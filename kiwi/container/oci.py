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
from kiwi.defaults import Defaults
from kiwi.path import Path
from kiwi.archive.tar import ArchiveTar
from kiwi.logger import log
from kiwi.runtime_config import RuntimeConfig
from kiwi.oci_tools import OCI


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
                'entry_command': ['/bin/bash', '-x'],
                'entry_subcommand': ['ls', '-l'],
                'maintainer': 'tux',
                'user': 'root',
                'workingdir': '/root',
                'expose_ports': ['80', '42'],
                'volumes': ['/var/log', '/tmp'],
                'environment': {'PATH': '/bin'},
                'labels': {'name': 'value'},
                'history': {
                    'created_by': 'some explanation here',
                    'comment': 'some comment here',
                    'author': 'tux'
                }
            }
    """
    def __init__(self, root_dir, custom_args=None):
        self.root_dir = root_dir
        self.oci_root_dir = None
        if custom_args:
            self.oci_config = custom_args
        else:
            self.oci_config = {}

        self.runtime_config = RuntimeConfig()

        # for builds inside the buildservice we include a reference to the
        # specific build. Thus disturl label only exists inside the
        # buildservice.
        if Defaults.is_buildservice_worker():
            bs_label = 'org.openbuildservice.disturl'
            # Do not label anything if any build service label is
            # already present
            if 'labels' not in self.oci_config or \
                    bs_label not in self.oci_config['labels']:
                self._append_buildservice_disturl_label()

        if 'container_name' not in self.oci_config:
            log.info(
                'No container configuration provided, '
                'using default container name "kiwi-container:latest"'
            )
            self.oci_config['container_name'] = \
                Defaults.get_default_container_name()
            self.oci_config['container_tag'] = \
                Defaults.get_default_container_tag()

        if 'container_tag' not in self.oci_config:
            self.oci_config['container_tag'] = \
                Defaults.get_default_container_tag()

        if 'entry_command' not in self.oci_config and \
                'entry_subcommand' not in self.oci_config:
            self.oci_config['entry_subcommand'] = \
                Defaults.get_default_container_subcommand()

        if 'history' not in self.oci_config:
            self.oci_config['history'] = {}
        if 'created_by' not in self.oci_config['history']:
            self.oci_config['history']['created_by'] = \
                Defaults.get_default_container_created_by()

        self.oci = OCI(self.oci_config['container_tag'])

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

        if base_image:
            Path.create(self.oci.container_dir)
            image_tar = ArchiveTar(base_image)
            image_tar.extract(self.oci.container_dir)

        self.oci.init_layout(bool(base_image))

        self.oci.unpack()
        self.oci.sync_rootfs(''.join([self.root_dir, os.sep]), exclude_list)
        self.oci.repack()

        if 'additional_tags' in self.oci_config:
            for tag in self.oci_config['additional_tags']:
                self.oci.add_tag(tag)

        self.oci.set_config(self.oci_config, bool(base_image))

        self.oci.garbage_collect()

        return self.pack_image_to_file(filename)

    def pack_image_to_file(self, filename):
        """
        Packs the oci image into the given filename.

        :param string filename: file name of the resulting packed image
        """
        oci_tarfile = ArchiveTar(filename)
        container_compressor = self.runtime_config.get_container_compression()
        if container_compressor:
            return oci_tarfile.create_xz_compressed(
                self.oci.container_dir,
                xz_options=self.runtime_config.get_xz_options()
            )
        else:
            return oci_tarfile.create(
                self.oci.container_dir
            )

    def _append_buildservice_disturl_label(self):
        with open(os.sep + Defaults.get_buildservice_env_name()) as env:
            for line in env:
                if line.startswith('BUILD_DISTURL') and '=' in line:
                    disturl = line.split('=')[1].lstrip('\'\"').rstrip('\n\'\"')
                    if disturl:
                        self.oci_config['labels'] = {
                            'org.openbuildservice.disturl': disturl
                        }
                        return
            log.warning('Could not find BUILD_DISTURL inside .buildenv')
