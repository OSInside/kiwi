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
           [--ignore-repos]
           [--set-repo=<source,type,alias,priority>]
           [--add-repo=<source,type,alias,priority>...]
           [--obs-repo-internal]
           [--add-package=<name>...]
           [--delete-package=<name>...]
       kiwi system prepare help

commands:
    prepare
        prepare and install a new system for chroot access
    prepare help
        show manual page for prepare command

options:
    --add-package=<name>
        install the given package name
    --add-repo=<source,type,alias,priority>
        add repository with given source, type, alias and priority.
    --delete-package=<name>
        delete the given package name
    --allow-existing-root
        allow to use an existing root directory. Use with caution
        this could cause an inconsistent root tree if the existing
        contents does not fit to the additional installation
    --description=<directory>
        the description must be a directory containing a kiwi XML
        description and optional metadata files
    --ignore-repos
        ignore all repos from the XML configuration
    --obs-repo-internal
        when using obs:// repos resolve them using the SUSE internal
        buildservice. This only works if access to SUSE's internal
        buildservice is granted
    --root=<directory>
        the path to the new root directory of the system
    --set-repo=<source,type,alias,priority>
        overwrite the repo source, type, alias or priority for the first
        repository in the XML description
"""
import os

# project
from .base import CliTask
from ..help import Help
from ..privileges import Privileges
from ..system.prepare import SystemPrepare
from ..system.setup import SystemSetup
from ..defaults import Defaults
from ..system.profile import Profile
from ..logger import log


class SystemPrepareTask(CliTask):
    """
    Implements preparation and installation of a new root system

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):
        """
        Prepare and install a new system for chroot access
        """
        self.manual = Help()
        if self._help():
            return

        Privileges.check_for_root_permissions()

        self.load_xml_description(
            self.command_args['--description']
        )
        self.runtime_checker.check_image_include_repos_http_resolvable()
        self.runtime_checker.check_target_directory_not_in_shared_cache(
            self.command_args['--root']
        )

        if self.command_args['--ignore-repos']:
            self.xml_state.delete_repository_sections()

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

        self.runtime_checker.check_repositories_configured()

        if os.path.exists('/.buildenv'):
            # This build runs inside of a buildservice worker. Therefore
            # the repo defintions is adapted accordingly
            self.xml_state.translate_obs_to_suse_repositories()

        elif self.command_args['--obs-repo-internal']:
            # This build should use the internal SUSE buildservice
            # Be aware that the buildhost has to provide access
            self.xml_state.translate_obs_to_ibs_repositories()

        package_requests = False
        if self.command_args['--add-package']:
            package_requests = True
        if self.command_args['--delete-package']:
            package_requests = True

        log.info('Preparing system')
        system = SystemPrepare(
            self.xml_state,
            self.command_args['--root'],
            self.command_args['--allow-existing-root']
        )
        manager = system.setup_repositories()
        system.install_bootstrap(manager)
        system.install_system(
            manager
        )
        if package_requests:
            if self.command_args['--add-package']:
                system.install_packages(
                    manager, self.command_args['--add-package']
                )
            if self.command_args['--delete-package']:
                system.delete_packages(
                    manager, self.command_args['--delete-package']
                )

        profile = Profile(self.xml_state)

        defaults = Defaults()
        defaults.to_profile(profile)

        setup = SystemSetup(
            self.xml_state, self.command_args['--root']
        )
        setup.import_shell_environment(profile)

        setup.import_description()
        setup.import_overlay_files()
        setup.call_config_script()
        setup.import_image_identifier()
        setup.setup_groups()
        setup.setup_users()
        setup.setup_keyboard_map()
        setup.setup_locale()
        setup.setup_timezone()

        system.pinch_system(
            manager=manager, force=True
        )

        # make sure system and manager instances are cleaned up now
        del system
        del manager

        # setup permanent image repositories after cleanup
        setup.import_repositories_marked_as_imageinclude()

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::prepare')
        else:
            return False
        return self.manual
