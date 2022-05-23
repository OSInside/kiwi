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
usage: kiwi-ng system prepare -h | --help
       kiwi-ng system prepare --description=<directory> --root=<directory>
           [--allow-existing-root]
           [--clear-cache]
           [--ignore-repos]
           [--ignore-repos-used-for-build]
           [--set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>]
           [--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>...]
           [--add-package=<name>...]
           [--add-bootstrap-package=<name>...]
           [--delete-package=<name>...]
           [--set-container-derived-from=<uri>]
           [--set-container-tag=<name>]
           [--add-container-label=<label>...]
           [--signing-key=<key-file>...]
       kiwi-ng system prepare help

commands:
    prepare
        prepare and install a new system for chroot access
    prepare help
        show manual page for prepare command

options:
    --add-bootstrap-package=<name>
        install the given package name as part of the early bootstrap process
    --add-package=<name>
        install the given package name
    --add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>
        add repository with given source, type, alias,
        priority, imageinclude(true|false), package_gpgcheck(true|false),
        list of signing_keys enclosed in curly brackets delimited by a colon,
        component list for debian based repos as string delimited by a space,
        main distribution name for debian based repos and
        repo_gpgcheck(true|false)
    --allow-existing-root
        allow to use an existing root directory. Use with caution
        this could cause an inconsistent root tree if the existing
        contents does not fit to the additional installation
    --clear-cache
        delete repository cache for each of the used repositories
        before installing any package
    --delete-package=<name>
        delete the given package name
    --description=<directory>
        the description must be a directory containing a kiwi XML
        description and optional metadata files
    --ignore-repos
        ignore all repos from the XML configuration
    --ignore-repos-used-for-build
        ignore all repos from the XML configuration except the
        ones marked as imageonly
    --root=<directory>
        the path to the new root directory of the system
    --set-container-derived-from=<uri>
        overwrite the source location of the base container
        for the selected image type. The setting is only effective
        if the configured image type is setup with an initial
        derived_from reference
    --set-container-tag=<name>
        overwrite the container tag in the container configuration.
        The setting is only effective if the container configuraiton
        provides an initial tag value
    --add-container-label=<name=value>
        add a container label in the container configuration metadata. It
        overwrites the label with the provided key-value pair in case it was
        already defined in the XML description
    --set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck>
        overwrite the first XML listed repository source, type, alias,
        priority, imageinclude(true|false), package_gpgcheck(true|false),
        list of signing_keys enclosed in curly brackets delimited by a colon,
        component list for debian based repos as string delimited by a space,
        main distribution name for debian based repos and
        repo_gpgcheck(true|false)
     --signing-key=<key-file>
        includes the key-file as a trusted key for package manager validations
"""
import os
import logging

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.privileges import Privileges
from kiwi.system.prepare import SystemPrepare
from kiwi.system.setup import SystemSetup
from kiwi.defaults import Defaults
from kiwi.system.profile import Profile
from kiwi.command import Command

log = logging.getLogger('kiwi')


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
            self.command_args['--description'], self.global_args['--kiwi-file']
        )

        abs_root_path = os.path.abspath(self.command_args['--root'])

        prepare_checks = self.checks_before_command_args
        prepare_checks.update(
            {
                'check_target_directory_not_in_shared_cache': [abs_root_path]
            }
        )
        self.run_checks(prepare_checks)

        if self.command_args['--ignore-repos']:
            self.xml_state.delete_repository_sections()
        elif self.command_args['--ignore-repos-used-for-build']:
            self.xml_state.delete_repository_sections_used_for_build()

        if self.command_args['--set-repo']:
            self.xml_state.set_repository(
                *self._get_repo_parameters(self.command_args['--set-repo'])
            )

        if self.command_args['--add-repo']:
            for add_repo in self.command_args['--add-repo']:
                self.xml_state.add_repository(
                    *self._get_repo_parameters(add_repo)
                )

        if self.command_args['--set-container-tag']:
            self.xml_state.set_container_config_tag(
                self.command_args['--set-container-tag']
            )

        if self.command_args['--add-container-label']:
            for add_label in self.command_args['--add-container-label']:
                try:
                    (name, value) = add_label.split('=', 1)
                    self.xml_state.add_container_config_label(name, value)
                except Exception:
                    log.warning(
                        'Container label {0} ignored. Invalid format: '
                        'expected labelname=value'.format(add_label)
                    )

        if self.command_args['--set-container-derived-from']:
            self.xml_state.set_derived_from_image_uri(
                self.command_args['--set-container-derived-from']
            )

        self.run_checks(self.checks_after_command_args)

        log.info('Preparing system')
        system = SystemPrepare(
            self.xml_state,
            abs_root_path,
            self.command_args['--allow-existing-root']
        )
        manager = system.setup_repositories(
            self.command_args['--clear-cache'],
            self.command_args[
                '--signing-key'
            ] + self.xml_state.get_repositories_signing_keys(),
            self.global_args['--target-arch']
        )
        run_bootstrap = True
        if self.xml_state.get_package_manager() == 'apt' and \
           self.command_args['--allow-existing-root']:
            # try to call apt-get inside of the existing root.
            # If the call succeeds we skip calling debootstrap again
            # and assume the root to be ok to proceed with apt-get
            # if it fails, treat the root as dirty and give the
            # bootstrap a try
            try:
                Command.run(['chroot', abs_root_path, 'apt-get', '--version'])
                run_bootstrap = False
                log.warning(
                    'debootstrap will only be called once, skipped'
                )
            except Exception:
                run_bootstrap = True

        if run_bootstrap:
            system.install_bootstrap(
                manager, self.command_args['--add-bootstrap-package']
            )

        setup = SystemSetup(
            self.xml_state, abs_root_path
        )
        setup.import_description()

        # call post_bootstrap.sh script if present
        setup.call_post_bootstrap_script()

        system.install_system(
            manager
        )

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

        profile.create(
            Defaults.get_profile_file(abs_root_path)
        )

        setup.import_overlay_files()
        setup.import_image_identifier()
        setup.setup_groups()
        setup.setup_users()
        setup.setup_keyboard_map()
        setup.setup_locale()
        setup.setup_plymouth_splash()
        setup.setup_timezone()
        setup.setup_permissions()
        setup.setup_selinux_file_contexts()

        # make sure manager instance is cleaned up now
        del manager

        # setup permanent image repositories after cleanup
        setup.import_repositories_marked_as_imageinclude()

        # call config.sh script if present
        setup.call_config_script()

        # handle uninstall package requests, gracefully uninstall
        # with dependency cleanup
        system.pinch_system(force=False)

        # handle delete package requests, forced uninstall without
        # any dependency resolution
        system.pinch_system(force=True)

        # delete any custom rpm macros created
        system.clean_package_manager_leftovers()

        # make sure system instance is cleaned up now
        del system

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::prepare')
        else:
            return False
        return self.manual

    def _get_repo_parameters(self, tokens):
        parameters = self.tentuple_token(tokens)
        signing_keys_index = 6
        if not parameters[signing_keys_index]:
            # make sure to pass empty list for signing_keys param
            parameters[signing_keys_index] = []
        return parameters
