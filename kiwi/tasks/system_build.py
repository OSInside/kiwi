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
from itertools import zip_longest
from urllib.parse import urlparse

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.system.prepare import SystemPrepare
from kiwi.system.setup import SystemSetup
from kiwi.builder import ImageBuilder
from kiwi.system.profile import Profile
from kiwi.defaults import Defaults
from kiwi.privileges import Privileges
from kiwi.path import Path

from kiwi.exceptions import (
    KiwiCATargetDistributionError
)

log = logging.getLogger('kiwi')


class SystemBuildTask(CliTask):
    """
    Implements building of system images

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):
        """
        Build a system image from the specified description. The
        build command combines the prepare and create commands
        """
        self.manual = Help()
        if self._help():
            return

        Privileges.check_for_root_permissions()

        abs_target_dir_path = os.path.abspath(
            self.command_args['--target-dir']
        )
        build_dir = os.sep.join([abs_target_dir_path, 'build'])
        image_root = os.sep.join([build_dir, 'image-root'])
        Path.create(build_dir)

        if not self.global_args['--logfile']:
            log.set_logfile(
                os.sep.join([abs_target_dir_path, 'build', 'image-root.log'])
            )

        self.load_xml_description(
            self.command_args['--description'], self.global_args['--kiwi-file']
        )

        build_checks = self.checks_before_command_args
        build_checks.update(
            {
                'check_target_directory_not_in_shared_cache':
                    [abs_target_dir_path],
                'check_target_dir_on_unsupported_filesystem':
                    [abs_target_dir_path]
            }
        )
        self.run_checks(build_checks)

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

        if self.command_args['--ca-cert']:
            ca_certs = self.command_args['--ca-cert']
            if ca_certs:
                target_distribution = \
                    self.command_args['--ca-target-distribution'] or \
                    self.xml_state.get_certificates_target_distribution()
                if not target_distribution or not Defaults.get_ca_update_map(
                    target_distribution
                ):
                    raise KiwiCATargetDistributionError(
                        'No or invalid CA target distribution, {} {}'.format(
                            'set via --ca-target-distribution.',
                            'allowed values are {}'.format(
                                Defaults.get_ca_target_distributions()
                            )
                        )
                    )
                for certificate in ca_certs:
                    self.xml_state.add_certificate(
                        certificate, target_distribution
                    )

        self.run_checks(self.checks_after_command_args)

        log.info('Preparing new root system')
        with SystemPrepare(
            self.xml_state,
            image_root,
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
                    self.xml_state, image_root
                )
                setup.import_description()

                # call post_bootstrap.sh script if present
                setup.call_post_bootstrap_script()

                # Setup custom CA certificates after bootstrap package install
                system.setup_ca_certificates()

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
                    Defaults.get_profile_file(image_root)
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

        setup.call_image_script()

        log.info('Creating system image')
        self.run_checks(
            {
                'check_dracut_module_versions_compatible_to_kiwi':
                    [image_root]
            }
        )
        image_builder = ImageBuilder.new(
            self.xml_state,
            abs_target_dir_path,
            image_root,
            custom_args={
                'signing_keys': self.command_args[
                    '--signing-key'
                ] + self.xml_state.get_repositories_signing_keys(),
                'xz_options': self.runtime_config.get_xz_options()
            }
        )
        result = image_builder.create()
        result.print_results()
        result.dump(
            os.sep.join([abs_target_dir_path, 'kiwi.result'])
        )

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::build')
        else:
            return False
        return self.manual

    def _get_repo_parameters(self, tokens, credentials):
        parameters = self.eleventuple_token(tokens)
        signing_keys_index = 6
        repo_source_index = 0
        repo_type_index = 1
        repo_alias_index = 2
        if not parameters[repo_type_index]:
            # make sure to pass a None value if an empty string
            # is provided as repo type. This will cause no type
            # attribute to be set instead of an empty type which
            # is not allowed by the schema
            parameters[repo_type_index] = None
        if not parameters[repo_alias_index]:
            # make sure to pass a None value if an empty string
            # is provided as repo alias. This will cause no alias
            # attribute to be set instead of an empty type which
            # is not allowed by the schema
            parameters[repo_alias_index] = None
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
