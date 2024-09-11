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
import os

# project
from kiwi.utils.temporary import Temporary
from kiwi.oci_tools.base import OCIBase
from kiwi.command import Command
from kiwi.path import Path
from kiwi.utils.command_capabilities import CommandCapabilities
from kiwi.defaults import Defaults


class OCIUmoci(OCIBase):
    """
    **Open Container Operations using umoci**
    """
    def post_init(self):
        """
        Initializes some umoci parameters and options
        """
        self.oci_dir_tempfile = Temporary(prefix='kiwi_oci_dir.').new_dir()
        self.oci_dir = self.oci_dir_tempfile.name
        self.container_dir = os.sep.join(
            [self.oci_dir, 'oci_layout']
        )
        self.working_image = '{0}:{1}'.format(
            self.container_dir, Defaults.get_container_base_image_tag()
        )
        if CommandCapabilities.has_option_in_help(
            'umoci', '--no-history', ['config', '--help'],
            raise_on_error=False
        ):
            self.no_history_flag = ['--no-history']
        else:
            self.no_history_flag = []

    def import_container_image(self, container_image_ref):
        """
        Imports container image reference to an OCI layout

        :param str container_image_ref: container image reference
        """
        Command.run(
            [
                'skopeo', 'copy', container_image_ref, 'oci:{0}:{1}'.format(
                    self.container_dir, Defaults.get_container_base_image_tag()
                )
            ] + (
                [
                    '--tmpdir', Defaults.get_temp_location()
                ] if self._skopeo_provides_tmpdir_option() else []
            )
        )

    def export_container_image(
        self, filename, transport, image_ref, additional_names=None
    ):
        """
        Exports the working container to a container image archive

        :param str filename: The resulting filename
        :param str transport: The archive format
        :param str image_name: Name of the exported image
        :param str image_tag: Tag of the exported image
        :param list additional_names: List of additional references
        """
        extra_tags_opt = []
        if additional_names:
            for ref in additional_names:
                extra_tags_opt.extend(['--additional-tag', ref])

        # make sure the target tar file does not exist
        # skopeo doesn't support force overwrite
        Path.wipe(filename)
        Command.run(
            [
                'skopeo', 'copy', 'oci:{0}'.format(self.working_image),
                '{0}:{1}:{2}'.format(transport, filename, image_ref)
            ] + extra_tags_opt + (
                [
                    '--tmpdir', Defaults.get_temp_location()
                ] if self._skopeo_provides_tmpdir_option() else []
            )
        )

    def init_container(self):
        """
        Initialize a new container layout

        :param bool base_image: True|False
        """
        Command.run(
            ['umoci', 'init', '--layout', self.container_dir]
        )
        Command.run(
            ['umoci', 'new', '--image', self.working_image]
        )

    def unpack(self):
        """
        Unpack current container root data
        """
        self.oci_root_dir_tempdir = Temporary(
            prefix='kiwi_oci_root_dir.'
        ).new_dir()
        self.oci_root_dir = self.oci_root_dir_tempdir.name
        Command.run([
            'umoci', 'unpack', '--image',
            self.working_image, self.oci_root_dir
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
            options=Defaults.get_sync_options() + [
                '--delete'
            ]
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
            options=Defaults.get_sync_options()
        )

    def repack(self, oci_config):
        """
        Pack root data directory into container image

        :param list oci_config: meta data list
        """
        history_flags = self._process_oci_history_to_arguments(oci_config)
        history_flags.extend(['--history.created', self.creation_date])
        Command.run(
            ['umoci', 'repack'] + history_flags + [
                '--image', self.working_image, self.oci_root_dir
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
            ] + config_args + self.no_history_flag + [
                '--image', self.working_image,
                '--tag', oci_config['container_tag'],
                '--created', self.creation_date
            ]
        )
        self.working_image = '{0}:{1}'.format(
            self.container_dir, oci_config['container_tag']
        )

    @staticmethod
    def _process_oci_config_to_arguments(oci_config):
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

        if 'stopsignal' in oci_config:
            arguments.append(
                '--config.stopsignal={0}'.format(oci_config['stopsignal'])
            )

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

    @staticmethod
    def _process_oci_history_to_arguments(oci_config):
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

    def post_process(self):
        """
        Cleanup unused data from operations
        """
        Command.run(
            ['umoci', 'gc', '--layout', self.container_dir]
        )
