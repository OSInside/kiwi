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
from itertools import zip_longest
from urllib.parse import urlparse

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.utils.output import DataOutput
from kiwi.solver.sat import Sat
from kiwi.solver.repository import SolverRepository
from kiwi.solver.repository.base import SolverRepositoryBase
from kiwi.system.uri import Uri
from kiwi.system.profile import Profile
from kiwi.defaults import Defaults


class ImageInfoTask(CliTask):
    """
    Implements retrieval of in depth information for an image description

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):
        """
        Walks through the given info options and provide the requested data
        """
        self.manual = Help()
        if self.command_args.get('help') is True:
            return self.manual.show('kiwi::image::info')

        self.load_xml_description(
            self.command_args['--description'], self.global_args['--kiwi-file']
        )

        if self.command_args['--ignore-repos']:
            self.xml_state.delete_repository_sections()

        if self.command_args['--add-repo']:
            for add_repo, add_credentials in zip_longest(
                self.command_args['--add-repo'],
                self.command_args['--add-repo-credentials']
            ):
                self.xml_state.add_repository(
                    *self._get_repo_parameters(add_repo, add_credentials)
                )

        self.runtime_checker.check_repositories_configured()

        result = {
            'image': self.xml_state.xml_data.get_name()
        }

        if self.command_args['--print-kiwi-env']:
            profile = Profile(self.xml_state)
            defaults = Defaults()
            defaults.to_profile(profile)
            result['kiwi_env'] = profile.get_settings()

        if self.command_args['--list-profiles']:
            result['profile_names'] = []
            for profiles_section in self.xml_state.xml_data.get_profiles():
                for profile in profiles_section.get_profile():
                    result['profile_names'].append(profile.get_name())

        if self.command_args['--resolve-package-list']:
            solver = self._setup_solver()
            boostrap_package_list = self.xml_state.get_bootstrap_packages()
            package_list = boostrap_package_list + \
                self.xml_state.get_system_packages()
            bootstrap_collection_type = \
                self.xml_state.get_bootstrap_collection_type()
            system_collection_type = \
                self.xml_state.get_system_collection_type()
            bootstrap_packages = solver.solve(
                boostrap_package_list, False,
                True if bootstrap_collection_type == 'onlyRequired' else False
            )
            solved_packages = solver.solve(
                self.xml_state.get_system_packages(), False,
                True if system_collection_type == 'onlyRequired' else False
            )
            solved_packages.update(bootstrap_packages)
            package_info = {}
            for package, metadata in sorted(list(solved_packages.items())):
                if package in package_list:
                    status = 'listed_in_kiwi_description'
                else:
                    status = 'added_by_dependency_solver'
                package_info[package] = {
                    'source': metadata.uri,
                    'installsize_bytes': int(metadata.installsize_bytes),
                    'arch': metadata.arch,
                    'version': metadata.version,
                    'status': status
                }
            result['resolved-packages'] = package_info

        if self.global_args['--color-output']:
            DataOutput(result, style='color').display()
        else:
            DataOutput(result).display()

        if self.command_args['--print-xml']:
            DataOutput.display_file(
                self.description.markup.get_xml_description(),
                'Description(XML):'
            )
        elif self.command_args['--print-yaml']:
            DataOutput.display_file(
                self.description.markup.get_yaml_description(),
                'Description(YAML):'
            )
        elif self.command_args['--print-toml']:
            DataOutput.display_file(
                self.description.markup.get_toml_description(),
                'Description(TOML):'
            )

    def _setup_solver(self):
        solver = Sat()
        for xml_repo in self.xml_state.get_repository_sections_used_for_build():
            repo_source = xml_repo.get_source().get_path()
            repo_sourcetype = xml_repo.get_sourcetype() or ''
            repo_user = xml_repo.get_username()
            repo_secret = xml_repo.get_password()
            repo_type = xml_repo.get_type()
            repo_dist = xml_repo.get_distribution()
            repo_components = xml_repo.get_components()
            if not repo_type:
                repo_type = SolverRepositoryBase(
                    Uri(uri=repo_source, source_type=repo_sourcetype),
                    repo_user, repo_secret
                ).get_repo_type()
            if repo_type == 'apt-deb':
                # Debian based repos can be setup for a specific
                # distribution including a list of individual components.
                # For each component of the selected distribution extra
                # repository metadata exists. In such a case we iterate
                # over the configured dist components and add them as
                # repository each.
                dist_type = solver.set_dist_type('deb')
                if repo_components and repo_dist:
                    for component in repo_components.split():
                        repo_source_for_component = os.sep.join(
                            [
                                repo_source.rstrip(os.sep), 'dists', repo_dist,
                                component, f'binary-{dist_type.get("arch")}'
                            ]
                        )
                        solver.add_repository(
                            SolverRepository.new(
                                Uri(
                                    repo_source_for_component,
                                    repo_type, repo_sourcetype
                                ),
                                repo_user, repo_secret
                            )
                        )
                    continue
            solver.add_repository(
                SolverRepository.new(
                    Uri(repo_source, repo_type, repo_sourcetype),
                    repo_user, repo_secret
                )
            )
        return solver

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
