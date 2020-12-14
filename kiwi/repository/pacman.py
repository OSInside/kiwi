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
from tempfile import NamedTemporaryFile

# project
from kiwi.repository.base import RepositoryBase
from kiwi.path import Path
from kiwi.command import Command


class RepositoryPacman(RepositoryBase):
    """
    **Implements repo handling for pacman package manager**

    :param str shared_pacman_dir: shared directory between image root
        and build system root
    :param str runtime_pacman_config_file: pacman runtime config file name
    :param list pacman_args: zypper caller args plus additional custom args
    :param dict command_env: customized os.environ for zypper
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom pacman arguments and create runtime configuration
        and environment

        :param list custom_args: pacman arguments
        """
        self.custom_args = custom_args
        self.check_signatures = False
        self.repo_names = []
        if not custom_args:
            self.custom_args = []

        self.runtime_pacman_config_file = NamedTemporaryFile(
            dir=self.root_dir
        )

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

    def use_default_location(self):
        """
        Setup pacman repository operations to store all data
        in the default places
        """
        self.shared_pacman_dir['repos-dir'] = \
            self.root_dir + '/etc/pacman.d'

    def runtime_config(self):
        """
        pacman runtime configuration and environment
        """
        return {
            'pacman_args': self.pacman_args,
            'command_env': os.environ
        }

    def _add_repo_section(
        self, config_parser, name, uri, repo_gpgcheck=None, pkg_gpgcheck=None
    ):
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
        self, name, uri, repo_type=None,
        prio=None, dist=None, components=None,
        user=None, secret=None, credentials_file=None,
        repo_gpgcheck=None, pkg_gpgcheck=None,
        sourcetype=None, use_for_bootstrap=False
    ):
        """
        Add pacman repository

        :param str name: repository base file name
        :param str uri: repository URI
        :param repo_type: unused
        :param int prio:
        :param dist: unused
        :param components: components to be used from this repository
        :param user: unused
        :param secret: unused
        :param credentials_file: unused
        :param bool repo_gpgcheck: enable database signature validation
        :param bool pkg_gpgcheck: enable package signature validation
        :param str sourcetype: unused
        :param bool use_for_bootstrap: unused
        """
        repo_file = '{0}/{1}.repo'.format(
            self.shared_pacman_dir['repos-dir'], name
        )
        self.repo_names.append(name + '.repo')
        repo_config = ConfigParser()
        repo_config.optionxform = str
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

    def import_trusted_keys(self, signing_keys):
        """
        zypper runtime configuration and environment
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

    def delete_repo(self, name):
        """
        Delete pacman repository

        :param str name: repository name
        """
        Path.wipe(
            '{0}/{1}.repo'.format(self.shared_pacman_dir['repos-dir'], name)
        )

    def delete_all_repos(self):
        """
        Delete all pacman repositories
        """
        Path.wipe(self.shared_pacman_dir['repos-dir'])
        Path.create(self.shared_pacman_dir['repos-dir'])

    def delete_repo_cache(self, name):
        """
        Delete pacman repository cache

        The method deletes these directories to cleanup the
        cache information

        :param str name: repository name
        """
        Path.wipe(self.shared_pacman_dir['cache-dir'])

    def setup_package_database_configuration(self):
        """
        Creates the folder that will contain the package manager database
        """
        Path.create(os.sep.join([self.root_dir, 'var/lib/pacman']))

    def cleanup_unused_repos(self):
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

    def _write_runtime_config(self):
        runtime_pacman_config = ConfigParser()
        runtime_pacman_config.optionxform = str
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
