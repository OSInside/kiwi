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
import sys
from typing import Dict, List, Optional
if sys.version_info >= (3, 8):
    from typing import TypedDict  # pragma: no cover
else:  # pragma: no cover
    from typing_extensions import TypedDict  # pragma: no cover

# project
from kiwi.utils.compress import Compress
from kiwi.runtime_config import RuntimeConfig
from kiwi.defaults import Defaults
from kiwi.oci_tools import OCI
from kiwi.container.base import ContainerImageBase

log = logging.getLogger('kiwi')


class OciConfig(TypedDict, total=False):
    container_name: str
    container_tag: str
    additional_names: List[str]
    entry_command: List[str]
    entry_subcommand: List[str]
    maintainer: str
    user: str
    workingdir: str
    expose_ports: List[str]
    volumes: List[str]
    environment: Dict[str, str]
    labels: Dict[str, str]
    history: Dict[str, str]


class ContainerImageOCI(ContainerImageBase):
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
            'additional_names': ['current', 'foobar'],
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
    def __init__(
        self, root_dir: str, transport: str,
        custom_args: Optional[OciConfig] = None
    ) -> None:
        self.root_dir = root_dir
        self.archive_transport = transport
        self.oci_config = custom_args or {}

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

    def create(
        self, filename: str, base_image: str,
        ensure_empty_tmpdirs: bool = True, compress_archive: bool = False
    ) -> str:
        """
        Create compressed oci system container tar archive

        :param string filename: archive file name
        :param string base_image: archive used as a base image
        :param bool ensure_empty_tmpdirs: exclude system tmp directories
        :param bool compress_archive: compress container archive
        """
        exclude_list = Defaults.\
            get_exclude_list_for_root_data_sync(
                ensure_empty_tmpdirs
            ) + Defaults.get_exclude_list_from_custom_exclude_files(
                self.root_dir
            )
        exclude_list.append('dev/*')
        exclude_list.append('sys/*')
        exclude_list.append('proc/*')

        with OCI.new() as oci:
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
                self.oci_config['container_name'],
                self.oci_config['container_tag']
            )

            oci.unpack()
            oci.sync_rootfs(self.root_dir, exclude_list)
            oci.repack(self.oci_config)
            oci.set_config(self.oci_config)
            oci.post_process()

            image_ref = '{0}:{1}'.format(
                self.oci_config['container_name'],
                self.oci_config['container_tag']
            )
            additional_refs: List[str] = []
            if self.archive_transport == 'docker-archive':
                if 'additional_names' in self.oci_config:
                    additional_refs = []
                    for name in self.oci_config['additional_names']:
                        name_parts = name.partition(':')
                        if not name_parts[0]:
                            additional_refs.append('{0}:{1}'.format(
                                self.oci_config['container_name'], name_parts[2]
                            ))
                        elif not name_parts[2]:
                            additional_refs.append('{0}:{1}'.format(
                                name_parts[0], self.oci_config['container_tag']
                            ))
                        else:
                            additional_refs.append('{0}:{1}'.format(
                                name_parts[0], name_parts[2]
                            ))

            oci.export_container_image(
                filename, self.archive_transport, image_ref, additional_refs
            )

        if compress_archive:
            compress = Compress(filename)
            filename = compress.xz(RuntimeConfig().get_xz_options())

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
