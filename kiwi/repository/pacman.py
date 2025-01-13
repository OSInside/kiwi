# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
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
from configparser import ConfigParser
from typing import (
    List, Dict
)

# project
import kiwi.defaults as defaults
from kiwi.utils.temporary import (
    Temporary, TmpT
)
from kiwi.repository.base import RepositoryBase
from kiwi.path import Path
from kiwi.command import Command
from kiwi.utils.toenv import ToEnv


class RepositoryPacman(RepositoryBase):
    """
    **Implements repo handling for pacman package manager**

    :param str shared_pacman_dir: shared directory between image root
        and build system root
    :param str runtime_pacman_config_file: pacman runtime config file name
    :param list pacman_args: pacman caller args plus additional custom args
    :param dict command_env: customized os.environ for pacman
    """

    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Store custom pacman arguments and create runtime configuration
        and environment

        :param list custom_args: pacman arguments
        """
        self.runtime_pacman_config_file = TmpT(name='')
        self.custom_args = custom_args
        self.check_signatures = False
        self.repo_names: List = []

        self.runtime_pacman_config_file = Temporary(
            path=self.root_dir, prefix='kiwi_pacman.conf'
        ).unmanaged_file()

        if 'check_signatures' in self.custom_args:
            self.custom_args.remove('check_signatures')
            self.check_signatures = True

        manager_base = self.shared_location + '/pacman'

        self.shared_pacman_dir = {
            'cache-dir': manager_base + '/cache',
            'repos-dir': manager_base + '/repos'
        }
        Path.create(self.shared_pacman_dir['repos-dir'])

        self.pacman_args = [
            '--config', self.runtime_pacman_config_file.name,
            '--noconfirm'
        ]

        self._write_runtime_config()

    def use_default_location(self) -> None:
        """
        Setup pacman repository operations to store all data
        in the default places
        """
        self.shared_pacman_dir['repos-dir'] = \
            self.root_dir + '/etc/pacman.d'

    def runtime_config(self) -> Dict:
        """
        pacman runtime configuration and environment
        """
        ToEnv(self.root_dir, defaults.PACKAGE_MANAGER_ENV_VARS)
        return {
            'pacman_args': self.pacman_args,
            'command_env': os.environ
        }

    def _add_repo_section(
        self, config_parser: ConfigParser, name: str, uri: str,
        repo_gpgcheck: bool = False, pkg_gpgcheck: bool = False
    ) -> None:
        config_parser.add_section(name)
        if uri.startswith(os.sep) and os.path.exists(uri):
            uri = 'file://{}'.format(uri)
        config_parser.set(name, 'Server', uri)
        config_parser.set(
            name, 'SigLevel', '{0} {1}'.format(
                'Required' if pkg_gpgcheck else 'Never',
                'DatabaseRequired' if repo_gpgcheck else 'DatabaseNever'
            )
        )

    def add_repo(
        self, name: str, uri: str, repo_type: str = None,
        prio: int = None, dist: str = None, components: str = None,
        user: str = None, secret: str = None, credentials_file: str = None,
        repo_gpgcheck: bool = False, pkg_gpgcheck: bool = False,
        sourcetype: str = None, customization_script: str = None,
        architectures: str = None
    ) -> None:
        """
        Add pacman repository

        :param str name: repository base file name
        :param str uri: repository URI
        :param str repo_type: unused
        :param int prio:
        :param dist: unused
        :param str components: components to be used from this repository
        :param str user: unused
        :param str secret: unused
        :param credentials_file: unused
        :param bool repo_gpgcheck: enable database signature validation
        :param bool pkg_gpgcheck: enable package signature validation
        :param str sourcetype: unused
        :param str customization_script:
            custom script called after the repo file was created
        :param str architectures: unused
        """
        repo_file = '{0}/{1}.repo'.format(
            self.shared_pacman_dir['repos-dir'], name
        )
        self.repo_names.append(name + '.repo')
        repo_config = ConfigParser()
        repo_config.optionxform = str  # type: ignore
        if not components:
            self._add_repo_section(
                repo_config, name, uri, repo_gpgcheck,
                pkg_gpgcheck
            )
        else:
            for component in components.split():
                self._add_repo_section(
                    repo_config, component, uri, repo_gpgcheck,
                    pkg_gpgcheck
                )

        with open(repo_file, 'w') as config:
            repo_config.write(config)
        if customization_script:
            self.run_repo_customize(customization_script, repo_file)

    def import_trusted_keys(self, signing_keys: List) -> None:
        """
        pacman runtime configuration and environment
        """
        for signing_key in signing_keys:
            if os.path.exists(signing_key):
                Command.run(
                    ['pacman-key', '--recv-keys', signing_key]
                )
            else:
                Command.run(
                    ['pacman-key', '--add', signing_key]
                )

    def delete_repo(self, name: str) -> None:
        """
        Delete pacman repository

        :param str name: repository name
        """
        Path.wipe(
            '{0}/{1}.repo'.format(self.shared_pacman_dir['repos-dir'], name)
        )

    def delete_all_repos(self) -> None:
        """
        Delete all pacman repositories
        """
        Path.wipe(self.shared_pacman_dir['repos-dir'])
        Path.create(self.shared_pacman_dir['repos-dir'])

    def delete_repo_cache(self, name: str) -> None:
        """
        Delete pacman repository cache

        The method deletes these directories to cleanup the
        cache information

        :param str name: repository name
        """
        Path.wipe(self.shared_pacman_dir['cache-dir'])

    def setup_package_database_configuration(self) -> None:
        """
        Creates the folder that will contain the package manager database
        """
        Path.create(os.sep.join([self.root_dir, 'var/lib/pacman']))

    def cleanup_unused_repos(self) -> None:
        """
        Delete unused pacman repositories

        Repository configurations which are not used for this build
        must be removed otherwise they are taken into account for
        the package installations
        """
        repos_dir = self.shared_pacman_dir['repos-dir']
        repo_files = list(os.walk(repos_dir))[0][2]
        for repo_file in repo_files:
            if repo_file not in self.repo_names:
                Path.wipe(repos_dir + '/' + repo_file)

    def _write_runtime_config(self) -> None:
        runtime_pacman_config = ConfigParser()
        runtime_pacman_config.optionxform = str  # type: ignore
        runtime_pacman_config.add_section('options')

        runtime_pacman_config.set(
            'options', 'Architecture', 'auto'
        )
        runtime_pacman_config.set(
            'options', 'CacheDir', self.shared_pacman_dir['cache-dir']
        )

        if self.check_signatures:
            runtime_pacman_config.set(
                'options', 'SigLevel', 'Required DatabaseRequired'
            )
            runtime_pacman_config.set(
                'options', 'LocalFileSigLevel', 'Required DatabaseRequired'
            )
        else:
            runtime_pacman_config.set(
                'options', 'SigLevel', 'Never DatabaseNever'
            )
            runtime_pacman_config.set(
                'options', 'LocalFileSigLevel', 'Never DatabaseNever'
            )

        runtime_pacman_config.set(
            'options', 'Include', '{0}/*.repo'.format(
                self.shared_pacman_dir['repos-dir']
            )
        )

        with open(self.runtime_pacman_config_file.name, 'w') as config:
            runtime_pacman_config.write(config)

    def cleanup(self) -> None:
        """
        Delete intermediate pacman config file
        """
        if os.path.isfile(self.runtime_pacman_config_file.name):
            os.unlink(self.runtime_pacman_config_file.name)
