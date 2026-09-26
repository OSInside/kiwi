# Copyright (c) 2021 SUSE Linux GmbH.  All rights reserved.
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
from textwrap import dedent

# project
from kiwi.help import Help
from kiwi.tasks.base import CliTask
from kiwi.privileges import Privileges
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState
from kiwi.oci_tools import OCI
from kiwi.utils.output import DataOutput
from kiwi.command import Command
from kiwi.path import Path
from kiwi.stackbuild.defaults import StackBuildDefaults

from kiwi.exceptions import KiwiStackBuildContainerNameInvalid

log = logging.getLogger('kiwi')


class SystemStashTask(CliTask):
    """
    Implements storing of an image root tree as OCI container,
    called a stash

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self) -> None:
        """
        Create a stash container from the given root directory
        or list the available stashes
        """
        self.manual = Help()
        if self.command_args.get('help') is True:
            return self.manual.show('kiwi::system::stash')

        if self.command_args.get('--list') is True:
            stash_dir = StackBuildDefaults.get_stash_home()
            stashes = DataOutput(
                {
                    stash_dir: os.listdir(
                        stash_dir
                    ) if os.path.isdir(stash_dir) else []
                }
            )
            stashes.display()
            return

        if self.command_args.get('--root'):
            Privileges.check_for_root_permissions()

            log.info('Reading Image description')
            kiwi_description = os.path.join(
                self.command_args['--root'], 'image', 'config.xml'
            )
            description = XMLDescription(kiwi_description)
            xml_state = XMLState(
                xml_data=description.load()
            )
            contact_info = xml_state.get_description_section()
            image_name = self.command_args.get('--container-name') or \
                xml_state.xml_data.get_name()
            if not StackBuildDefaults.is_container_name_valid(image_name):
                message = dedent('''\n
                    Image name {0!r} cannot be used as container name

                    Container names must start or end with a letter or number,
                    and can contain only letters, numbers, and the dash (-)
                    character. The name attribute in the KIWI description at:
                    {1}
                    does not conform to this requirement

                    Please provide an alternative stash name via the

                      --container-name <name>

                    option
                ''')
                raise KiwiStackBuildContainerNameInvalid(
                    message.format(
                        image_name, kiwi_description
                    )
                )
            stash_target_dir = SystemStashTask._create_stash_target_dir(
                image_name
            )

            stash_container_file_name = os.path.join(
                stash_target_dir, f'{image_name}.tar'
            )
            stash_container_tag = self.command_args.get('--tag') or 'latest'
            container_config = StackBuildDefaults.get_container_config(
                image_name, stash_container_tag, contact_info.author
            )
            log.info('Initializing stash container')
            oci = OCI.new()
            if os.path.isfile(stash_container_file_name):
                log.info('--> Adding new layer on existing stash')
                oci.import_container_image(
                    f'oci-archive:{stash_container_file_name}:'
                    f'{image_name}:{stash_container_tag}'
                )
            else:
                log.info('--> Creating initial layer')
                oci.init_container()

            oci.unpack()
            oci.sync_rootfs(
                self.command_args['--root'],
                StackBuildDefaults.get_stash_exclude_list()
            )
            oci.repack(container_config)
            oci.set_config(container_config)
            oci.post_process()
            log.info('Exporting stash container')
            oci.export_container_image(
                stash_container_file_name, 'oci-archive',
                f'{image_name}:{stash_container_tag}'
            )
            log.info('Importing stash to local registry')
            Command.run(
                ['podman', 'load', '-i', stash_container_file_name]
            )

    @staticmethod
    def _create_stash_target_dir(image_name: str) -> str:
        stash_target_dir = os.path.join(
            StackBuildDefaults.get_stash_home(),
            image_name
        )
        Path.create(stash_target_dir)
        return stash_target_dir
