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
usage: kiwi image info -h | --help
       kiwi image info --description=<directory>
           [--resolve-package-list]
           [--ignore-repos]
           [--add-repo=<source,type,alias,priority>...]
       kiwi image info help

commands:
    info
        provide information about the specified image description

options:
    --add-repo=<source,type,alias,priority>
        add repository with given source, type, alias and priority
    --description=<directory>
        the description must be a directory containing a kiwi XML
        description and optional metadata files
    --ignore-repos
        ignore all repos from the XML configuration
    --resolve-package-list
        solve package dependencies and return a list of all
        packages including their attributes e.g size,
        shasum, etc...
"""
# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.utils.output import DataOutput
from kiwi.solver.sat import Sat
from kiwi.solver.repository import SolverRepository
from kiwi.system.uri import Uri


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
            self.command_args['--description']
        )

        if self.command_args['--ignore-repos']:
            self.xml_state.delete_repository_sections()

        if self.command_args['--add-repo']:
            for add_repo in self.command_args['--add-repo']:
                (repo_source, repo_type, repo_alias, repo_prio) = \
                    self.quadruple_token(add_repo)
                self.xml_state.add_repository(
                    repo_source, repo_type, repo_alias, repo_prio
                )

        self.runtime_checker.check_repositories_configured()

        result = {
            'image': self.xml_state.xml_data.get_name()
        }

        if self.command_args['--resolve-package-list']:
            solver = self._setup_solver()
            boostrap_package_list = self.xml_state.get_bootstrap_packages()
            package_list = boostrap_package_list + \
                self.xml_state.get_system_packages()
            bootstrap_packages = solver.solve(
                boostrap_package_list, False,
                True if self.xml_state.get_bootstrap_collection_type() is
                'onlyRequired' else False
            )
            solved_packages = solver.solve(
                self.xml_state.get_system_packages(), False,
                True if self.xml_state.get_system_collection_type() is
                'onlyRequired' else False
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

    def _setup_solver(self):
        solver = Sat()
        for xml_repo in self.xml_state.get_repository_sections_used_for_build():
            repo_source = xml_repo.get_source().get_path()
            repo_user = xml_repo.get_username()
            repo_secret = xml_repo.get_password()
            repo_type = xml_repo.get_type()
            solver.add_repository(
                SolverRepository(
                    Uri(repo_source, repo_type), repo_user, repo_secret
                )
            )
        return solver
