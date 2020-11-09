# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms owf the GNU General Public License as published by
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
import logging
import os
import random
import string

# project
from kiwi.oci_tools.base import OCIBase
from kiwi.command import Command
from kiwi.path import Path
from kiwi.defaults import Defaults
from kiwi.exceptions import KiwiBuildahError

log = logging.getLogger('kiwi')


class OCIBuildah(OCIBase):
    """
    **Open Container Operations using buildah**
    """
    def post_init(self):
        """
        Initializes some default parameters
        """
        self.working_image = None
        self.imported_image = None
        self.working_container = None

    def import_container_image(self, container_image_ref):
        """
        Imports container image reference to the OCI containers storage.

        :param str container_image_ref: container image reference
        """
        if not self.imported_image:
            self.imported_image = 'kiwi-image-{0}:{1}'.format(
                self._random_string_generator(),
                Defaults.get_container_base_image_tag()
            )
        else:
            raise KiwiBuildahError(
                "Image already imported, called: '{0}'".format(
                    self.imported_image
                )
            )

        # We are making use of skopeo instead of only calling 'buildah from'
        # because we want to control the image name loaded into the containers
        # storage. This way we are certain to not leave any left over after the
        # build.
        Command.run(
            [
                'skopeo', 'copy', container_image_ref,
                'containers-storage:{0}'.format(self.imported_image)
            ]
        )

        if not self.working_container:
            self.working_container = 'kiwi-container-{0}'.format(
                self._random_string_generator()
            )
        else:
            raise KiwiBuildahError(
                "Container already initated, called: '{0}'".format(
                    self.working_container
                )
            )

        Command.run(
            [
                'buildah', 'from', '--name', self.working_container,
                'containers-storage:{0}'.format(self.imported_image)
            ]
        )

    def export_container_image(
        self, filename, transport, image_ref, additional_refs=None
    ):
        """
        Exports the working container to a container image archive

        :param str filename: The resulting filename
        :param str transport: The archive format
        :param str image_name: Name of the exported image
        :param str image_tag: Tag of the exported image
        :param list additional_tags: List of additional references
        """
        extra_tags_opt = []
        if additional_refs:
            for ref in additional_refs:
                extra_tags_opt.extend(['--additional-tag', ref])

        # make sure the target tar file does not exist
        # skopeo doesn't support force overwrite
        Path.wipe(filename)
        if self.working_image:
            export_image = self.working_image
        elif self.imported_image:
            export_image = self.imported_image
        else:
            raise KiwiBuildahError("There is no image to export defined")

        # we are using 'skopeo copy' to export images instead of 'buildah push'
        # because buildah does not support multiple tags
        Command.run([
            'skopeo', 'copy', 'containers-storage:{0}'.format(export_image),
            '{0}:{1}:{2}'.format(transport, filename, image_ref)
        ] + extra_tags_opt)

    def init_container(self):
        """
        Initialize a new container in OCI containers storage
        """
        if not self.working_container:
            self.working_container = 'kiwi-container-{0}'.format(
                self._random_string_generator()
            )
        else:
            raise KiwiBuildahError(
                "Image already imported or initated at '{0}' container".format(
                    self.working_container
                )
            )

        Command.run(
            ['buildah', 'from', '--name', self.working_container, 'scratch']
        )

    def unpack(self):
        """
        Mounts current container root data to a directory
        """
        cmd = Command.run(
            ['buildah', 'mount', self.working_container]
        )
        self.oci_root_dir = cmd.output.rstrip()

    def sync_rootfs(self, root_dir, exclude_list=None):
        """
        Synchronizes the image root with the rootfs of the container

        :param string root_dir: root directory of the prepare step
        :param list exclude_list: list of paths to exclude
        """
        self._sync_data(
            ''.join([root_dir, os.sep]), self.oci_root_dir,
            exclude_list=exclude_list,
            options=Defaults.get_sync_options() + ['--delete']
        )

    def import_rootfs(self, root_dir, exclude_list=None):
        """
        Synchronizes the container rootfs with the root tree of the build

        :param string root_dir: root directory used in prepare step
        :param list exclude_list: list of paths to exclude
        """
        self._sync_data(
            os.sep.join([self.oci_root_dir, '']), root_dir,
            exclude_list=exclude_list,
            options=Defaults.get_sync_options()
        )

    def repack(self, oci_config):
        """
        Pack root data directory into container image

        :param list oci_config: unused parameter
        """
        Command.run(
            ['buildah', 'umount', self.working_container]
        )

    def set_config(self, oci_config):
        """
        Set list of meta data information such as entry_point,
        maintainer, etc... to the container.

        :param list oci_config: meta data list
        :param bool base_image: True|False
        """
        config_args = self._process_oci_config_to_arguments(oci_config)
        Command.run(
            ['buildah', 'config'] + config_args + [self.working_container]
        )

    def post_process(self):
        """
        Commits the OCI container into an OCI image
        """
        if not self.working_image and self.working_container:
            self.working_image = 'kiwi-image-{0}:{1}'.format(
                self._random_string_generator(), 'tag-{0}'.format(
                    self._random_string_generator()
                )
            )
        else:
            raise KiwiBuildahError(
                "No container to commit or container already committed"
            )

        output = Command.run(
            [
                'buildah', 'commit', '--rm', '--format', 'oci',
                self.working_container, self.working_image
            ]
        )
        self.working_image = output.output.rstrip()
        self.working_container = None

    @classmethod
    def _process_oci_config_to_arguments(self, oci_config):
        """
        Process the oci configuration dictionary into a list of arguments
        for the 'buildah config' command

        :param list oci_config: meta data list

        :return: List of buildah config arguments

        :rtype: list
        """
        arguments = []
        if 'maintainer' in oci_config:
            arguments.append(
                '--author={0}'.format(oci_config['maintainer'])
            )

        if 'user' in oci_config:
            arguments.append(
                '--user={0}'.format(oci_config['user'])
            )

        if 'workingdir' in oci_config:
            arguments.append(
                '--workingdir={0}'.format(oci_config['workingdir'])
            )

        if 'entry_command' in oci_config:
            arguments.append('--entrypoint=[{0}]'.format(
                ','.join(
                    ['"{0}"'.format(x) for x in oci_config['entry_command']]
                )
            ))

        if 'entry_subcommand' in oci_config:
            arguments.append('--cmd={0}'.format(
                ' '.join(oci_config['entry_subcommand'])
            ))

        if 'volumes' in oci_config:
            for vol in oci_config['volumes']:
                arguments.append('--volume={0}'.format(vol))

        if 'expose_ports' in oci_config:
            for port in oci_config['expose_ports']:
                arguments.append('--port={0}'.format(port))

        if 'environment' in oci_config:
            for name in sorted(oci_config['environment']):
                arguments.append('--env={0}={1}'.format(
                    name, oci_config['environment'][name]
                ))

        if 'labels' in oci_config:
            for name in sorted(oci_config['labels']):
                arguments.append('--label={0}={1}'.format(
                    name, oci_config['labels'][name]
                ))

        if 'history' in oci_config:
            if 'comment' in oci_config['history']:
                arguments.append('--history-comment={0}'.format(
                    oci_config['history']['comment']
                ))
            if 'created_by' in oci_config['history']:
                arguments.append('--created-by={0}'.format(
                    oci_config['history']['created_by']
                ))
            if 'author' in oci_config['history']:
                log.warning('Author field in history is ignored using buildah')

        return arguments

    @classmethod
    def _random_string_generator(
        cls, chars_num=6, allchars=string.ascii_lowercase + string.digits
    ):
        """
        Creates a random string with the given length of characters choosen
        randomly from a given list of possible characters.

        Buildah makes use of the hosts configured containers storage of OCI
        images. This method is used to avoid name collisions with any
        previous image or container present in the host.

        :param int chars_num: Lenght of the generated random string
        :param list allchars: List of possible characters

        :return: generated random string

        :rtype: string
        """
        return "".join(random.choice(allchars) for x in range(chars_num))

    def __del__(self):
        if self.working_container:
            Command.run(['buildah', 'umount', self.working_container])
            Command.run(['buildah', 'rm', self.working_container])
        if self.working_image:
            Command.run(['buildah', 'rmi', self.working_image])
        if self.imported_image:
            Command.run(['buildah', 'rmi', self.imported_image])
