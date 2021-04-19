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
import logging

# project
from kiwi.defaults import Defaults
from kiwi.runtime_config import RuntimeConfig
from kiwi.oci_tools import OCI
from kiwi.utils.compress import Compress

log = logging.getLogger('kiwi')


class ContainerImageOCI:
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
    def __init__(self, root_dir, transport, custom_args=None):
        self.root_dir = root_dir
        self.archive_transport = transport
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
            # Do not label anything if the build service label is
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

        if 'history' not in self.oci_config:
            self.oci_config['history'] = {}
        if 'created_by' not in self.oci_config['history']:
            self.oci_config['history']['created_by'] = \
                Defaults.get_default_container_created_by()

    def create(self, filename, base_image):
        """
        Create compressed oci system container tar archive

        :param string filename: archive file name
        :param string base_image: archive used as a base image
        """
        exclude_list = Defaults.\
            get_exclude_list_for_root_data_sync() + Defaults.\
            get_exclude_list_from_custom_exclude_files(self.root_dir)
        exclude_list.append('dev/*')
        exclude_list.append('sys/*')
        exclude_list.append('proc/*')

        oci = OCI.new()
        if base_image:
            oci.import_container_image(
                'oci-archive:{0}:{1}'.format(
                    base_image, Defaults.get_container_base_image_tag()
                )
            )
        else:
            # Apply default subcommand only for base images
            if 'entry_command' not in self.oci_config and \
                    'entry_subcommand' not in self.oci_config:
                self.oci_config['entry_subcommand'] = \
                    Defaults.get_default_container_subcommand()
            oci.init_container()

        image_ref = '{0}:{1}'.format(
            self.oci_config['container_name'], self.oci_config['container_tag']
        )

        oci.unpack()
        oci.sync_rootfs(self.root_dir, exclude_list)
        oci.repack(self.oci_config)
        oci.set_config(self.oci_config)
        oci.post_process()

        if self.archive_transport == 'docker-archive':
            image_ref = '{0}:{1}'.format(
                self.oci_config['container_name'],
                self.oci_config['container_tag']
            )
            additional_refs = []
            if 'additional_tags' in self.oci_config:
                additional_refs = []
                for tag in self.oci_config['additional_tags']:
                    additional_refs.append('{0}:{1}'.format(
                        self.oci_config['container_name'], tag
                    ))
        else:
            image_ref = self.oci_config['container_tag']
            additional_refs = []

        oci.export_container_image(
            filename, self.archive_transport, image_ref, additional_refs
        )

        if self.runtime_config.get_container_compression():
            compressor = Compress(filename)
            return compressor.xz(self.runtime_config.get_xz_options())
        else:
            return filename

    def _append_buildservice_disturl_label(self):
        with open(os.sep + Defaults.get_buildservice_env_name()) as env:
            for line in env:
                if line.startswith('BUILD_DISTURL') and '=' in line:
                    disturl = line.split('=')[1].lstrip('\'\"').rstrip('\n\'\"')
                    if disturl:
                        label = {'org.openbuildservice.disturl': disturl}
                        if self.oci_config.get('labels'):
                            self.oci_config['labels'].update(label)
                        else:
                            self.oci_config['labels'] = label
                        return
            log.warning('Could not find BUILD_DISTURL inside .buildenv')
