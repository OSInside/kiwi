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
usage: kiwi system prepare -h | --help
       kiwi system prepare --description=<directory> --root=<directory>
           [--allow-existing-root]
           [--set-repo=<source,type,alias,priority>]
           [--add-repo=<source,type,alias,priority>...]
       kiwi system prepare help

commands:
    prepare
        prepare and install a new system for chroot access
    prepare help
        show manual page for prepare command

options:
    --description=<directory>
        the description must be a directory containing a kiwi XML
        description and optional metadata files
    --root=<directory>
        the path to the new root directory of the system
    --allow-existing-root
        allow to use an existing root directory. Use with caution
        this could cause an inconsistent root tree if the existing
        contents does not fit to the additional installation
    --set-repo=<source,type,alias,priority>
        overwrite the repo source, type, alias or priority for the first
        repository in the XML description
    --add-repo=<source,type,alias,priority>
        add repository with given source, type, alias and priority.
"""
# project
from cli_task import CliTask
from help import Help
from privileges import Privileges
from system import System
from system_setup import SystemSetup
from defaults import Defaults
from profile import Profile
from logger import log


class SystemPrepareTask(CliTask):
    """
        Implements preparation and installation of a new root system
    """
    def process(self):
        self.manual = Help()
        if self.__help():
            return

        Privileges.check_for_root_permissions()

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

        if self.command_args['prepare']:
            log.info('Preparing system')
            system = System(
                self.xml_state,
                self.command_args['--root'],
                self.command_args['--allow-existing-root']
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
                self.command_args['--root']
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

    def __help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::prepare')
        else:
            return False
        return self.manual
