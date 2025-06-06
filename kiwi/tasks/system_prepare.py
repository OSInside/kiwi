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
           [--set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck,repo_sourcetype>]
           [--set-repo-credentials=<user:pass_or_filename>]
           [--add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck,repo_sourcetype>...]
           [--add-repo-credentials=<user:pass_or_filename>...]
           [--add-package=<name>...]
           [--add-bootstrap-package=<name>...]
           [--delete-package=<name>...]
           [--set-container-derived-from=<uri>]
           [--set-container-tag=<name>]
           [--add-container-label=<label>...]
           [--set-type-attr=<attribute=value>...]
           [--set-release-version=<version>]
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
    --add-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck,repo_sourcetype>
        add repository with given source, type, alias,
        priority, imageinclude(true|false), package_gpgcheck(true|false),
        list of signing_keys enclosed in curly brackets delimited by a colon,
        component list for debian based repos as string delimited by a space,
        main distribution name for debian based repos,
        repo_gpgcheck(true|false) and repo_sourcetype(metalink|baseurl|mirrorlist)
    --add-repo-credentials=<user:pass_or_filename>
        for uri://user:pass@location type repositories, set the user and
        password connected with an add-repo specification. The first
        add-repo-credentials is connected with the first add-repo
        specification and so on. If the provided value describes a
        filename in the filesystem, the first line of that file
        is read and used as credentials information.
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
    --set-repo=<source,type,alias,priority,imageinclude,package_gpgcheck,{signing_keys},components,distribution,repo_gpgcheck,repo_sourcetype>
        overwrite the first XML listed repository source, type, alias,
        priority, imageinclude(true|false), package_gpgcheck(true|false),
        list of signing_keys enclosed in curly brackets delimited by a colon,
        component list for debian based repos as string delimited by a space,
        main distribution name for debian based repos,
        repo_gpgcheck(true|false) and repo_sourcetype(metalink|baseurl|mirrorlist)
     --set-repo-credentials=<user:pass_or_filename>
        for uri://user:pass@location type repositories, set the user and
        password connected to the set-repo specification. If the provided
        value describes a filename in the filesystem, the first line of that
        file is read and used as credentials information.
     --set-type-attr=<attribute=value>
        overwrite/set the attribute with the provided value in the selected
        build type section
    --set-release-version=<version>
        overwrite/set the release-version element in the selected
        build type preferences section
     --signing-key=<key-file>
        includes the key-file as a trusted key for package manager validations
"""
import os
import logging
from itertools import zip_longest
from urllib.parse import urlparse

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.privileges import Privileges
from kiwi.system.prepare import SystemPrepare
from kiwi.system.setup import SystemSetup
from kiwi.defaults import Defaults
from kiwi.system.profile import Profile

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
                'check_target_directory_not_in_shared_cache': [abs_root_path],
                'check_target_dir_on_unsupported_filesystem': [abs_root_path]
            }
        )
        self.run_checks(prepare_checks)

        if self.command_args['--set-type-attr']:
            for set_type_attr in self.command_args['--set-type-attr']:
                (attribute, value) = self.attr_token(set_type_attr)
                log.info(f'--> Set <type ... {attribute}="{value}" .../>')
                try:
                    eval(
                        f'self.xml_state.build_type.set_{attribute}("{value}")'
                    )
                except AttributeError as issue:
                    log.error(f'Failed to set type attribute: {issue}')
                    return

        if self.command_args['--set-release-version']:
            release_version = self.command_args['--set-release-version']
            log.info(f'--> Set <release-version> = {release_version}')
            section_overwrite = False
            for preferences in self.xml_state.get_preferences_sections():
                section = preferences.get_release_version()
                if section:
                    section[0] = release_version
                    section_overwrite = True
                    break
            if not section_overwrite:
                preferences = self.xml_state.get_preferences_sections()[0]
                preferences.add_release_version(release_version)

        if self.command_args['--ignore-repos']:
            self.xml_state.delete_repository_sections()
        elif self.command_args['--ignore-repos-used-for-build']:
            self.xml_state.delete_repository_sections_used_for_build()

        if self.command_args['--set-repo']:
            self.xml_state.set_repository(
                *self._get_repo_parameters(
                    self.command_args['--set-repo'],
                    self.command_args['--set-repo-credentials']
                )
            )

        if self.command_args['--add-repo']:
            for add_repo, add_credentials in zip_longest(
                self.command_args['--add-repo'],
                self.command_args['--add-repo-credentials']
            ):
                self.xml_state.add_repository(
                    *self._get_repo_parameters(add_repo, add_credentials)
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
        with SystemPrepare(
            self.xml_state,
            abs_root_path,
            self.command_args['--allow-existing-root']
        ) as system:
            with system.setup_repositories(
                self.command_args['--clear-cache'],
                self.command_args[
                    '--signing-key'
                ] + self.xml_state.get_repositories_signing_keys(),
                self.global_args['--target-arch']
            ) as manager:
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
                setup.import_files()
                setup.setup_registry_import()

                # setup permanent image repositories after cleanup
                setup.import_repositories_marked_as_imageinclude()

                # call config.sh script if present
                setup.call_config_script()

                # if configured, assign SELinux labels
                setup.setup_selinux_file_contexts()

                # handle uninstall package requests, gracefully uninstall
                # with dependency cleanup
                system.pinch_system(force=False)

                # handle delete package requests, forced uninstall without
                # any dependency resolution
                system.pinch_system(force=True)

                # create file list of packages if requested
                setup.create_system_files()

                # delete any custom rpm macros created
                system.clean_package_manager_leftovers()

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::prepare')
        else:
            return False
        return self.manual

    def _get_repo_parameters(self, tokens, credentials):
        parameters = self.eleventuple_token(tokens)
        signing_keys_index = 6
        repo_source_index = 0
        if not parameters[signing_keys_index]:
            # make sure to pass empty list for signing_keys param
            parameters[signing_keys_index] = []
        if credentials:
            if os.path.isfile(credentials):
                credentials_data = open(credentials).readline().strip(os.linesep)
                os.unlink(credentials)
                credentials = credentials_data
            repo_source = parameters[repo_source_index]
            repo_scheme = urlparse(repo_source).scheme
            if repo_scheme:
                repo_source = repo_source.replace(f'{repo_scheme}://', '')
                repo_source = f'{repo_scheme}://{credentials}@{repo_source}'
                parameters[repo_source_index] = repo_source
        return parameters
