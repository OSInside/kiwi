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
"""
usage: kiwi system build -h | --help
       kiwi system build --description=<directory> --target-dir=<directory>
           [--set-repo=<source,type,alias,priority>]
           [--add-repo=<source,type,alias,priority>...]
       kiwi system build help

commands:
    build
        build a system image from the specified description. The
        build command combines the prepare and create commands
    build help
        show manual page for build command

options:
    --description=<directory>
        the description must be a directory containing a kiwi XML
        description and optional metadata files
    --target-dir=<directory>
        the target directory to store the system image file(s)
    --set-repo=<source,type,alias,priority>
        overwrite the repo source, type, alias or priority for the first
        repository in the XML description
    --add-repo=<source,type,alias,priority>
        add repository with given source, type, alias and priority.
"""
import os

# project
from cli_task import CliTask
from help import Help
from system import System
from system_setup import SystemSetup
from profile import Profile
from defaults import Defaults
from archive_builder import ArchiveBuilder
from filesystem_builder import FileSystemBuilder
from container_builder import ContainerBuilder
from disk_builder import DiskBuilder
from live_image_builder import LiveImageBuilder
from pxe_builder import PxeBuilder
from privileges import Privileges
from path import Path
from logger import log

from exceptions import (
    KiwiRequestedTypeError,
    KiwiNotImplementedError
)


class SystemBuildTask(CliTask):
    """
        Implements building of system images
    """
    def process(self):
        self.manual = Help()
        if self.__help():
            return

        Privileges.check_for_root_permissions()

        image_root = self.command_args['--target-dir'] + '/build/image-root'
        Path.create(image_root)

        if not self.global_args['--logfile']:
            log.set_logfile(
                self.command_args['--target-dir'] + '/build/image-root.log'
            )

        self.load_xml_description(
            self.command_args['--description']
        )

        if self.command_args['--set-repo']:
            (repo_source, repo_type, repo_alias, repo_prio) = \
                self.quadruple_token(self.command_args['--set-repo'])
            self.xml_state.set_repository(
                repo_source, repo_type, repo_alias, repo_prio
            )

        if self.command_args['--add-repo']:
            for add_repo in self.command_args['--add-repo']:
                (repo_source, repo_type, repo_alias, repo_prio) = \
                    self.quadruple_token(add_repo)
                self.xml_state.add_repository(
                    repo_source, repo_type, repo_alias, repo_prio
                )

                Path.create(self.command_args['--target-dir'])

        result = None
        if self.command_args['build']:
            log.info('Preparing new root system')

            system = System(
                self.xml_state, image_root, True
            )
            manager = system.setup_repositories()
            system.install_bootstrap(manager)
            system.install_system(
                manager
            )

            profile = Profile(self.xml_state)

            defaults = Defaults()
            defaults.to_profile(profile)

            setup = SystemSetup(
                self.xml_state,
                self.command_args['--description'],
                image_root
            )
            setup.import_shell_environment(profile)

            setup.import_description()
            setup.import_overlay_files()
            setup.call_config_script()
            setup.import_image_identifier()
            setup.setup_groups()
            setup.setup_users()
            setup.setup_hardware_clock()
            setup.setup_keyboard_map()
            setup.setup_locale()
            setup.setup_timezone()

            system.pinch_system(
                manager
            )
            # make sure destructors cleanup the new root system
            # before creating an image from the tree
            del setup
            del system

            log.info('Creating system image')
            requested_image_type = self.xml_state.get_build_type_name()
            if requested_image_type in Defaults.get_filesystem_image_types():
                filesystem = FileSystemBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    image_root
                )
                result = filesystem.create()
            elif requested_image_type in Defaults.get_disk_image_types():
                disk = DiskBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    image_root
                )
                result = disk.create()
            elif requested_image_type in Defaults.get_live_image_types():
                live_iso = LiveImageBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    image_root
                )
                result = live_iso.create()
            elif requested_image_type in Defaults.get_network_image_types():
                pxe = PxeBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    image_root
                )
                result = pxe.create()
            elif requested_image_type in Defaults.get_archive_image_types():
                archive = ArchiveBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    image_root
                )
                result = archive.create()
            elif requested_image_type in Defaults.get_container_image_types():
                container = ContainerBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    image_root
                )
                result = container.create()
            else:
                raise KiwiRequestedTypeError(
                    'requested image type %s not supported' %
                    requested_image_type
                )

            if result:
                result.print_results()
                result.dump(
                    self.command_args['--target-dir'] + '/kiwi.result'
                )

    def __help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::build')
        else:
            return False
        return self.manual
