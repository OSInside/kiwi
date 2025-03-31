# Copyright (c) 2025 SUSE LLC.  All rights reserved.
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
from typing import (
    List, Dict
)

# project
from kiwi.defaults import Defaults
from kiwi.repository.base import RepositoryBase
from kiwi.path import Path

log = logging.getLogger('kiwi')


class RepositoryApk(RepositoryBase):
    """
    **Implements repository handling for apk (Alpine) package manager**
    """
    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Store custom apk arguments and create runtime configuration
        and environment

        :param list custom_args: apk arguments
        """
        self.bootstrap_repo = ''
        self.custom_args = custom_args
        self.repo_dict: Dict[str, str] = {}
        self.signing_keys: List = []
        self.repo_config = os.sep.join(
            [self.root_dir, Defaults.get_apk_repo_config()]
        )
        self.command_env = self._create_apk_get_runtime_environment()
        Path.create(os.path.dirname(self.repo_config))

    def setup_package_database_configuration(self) -> None:
        """
        Setup package database configuration

        No special database configuration required for apk
        """
        pass

    def use_default_location(self) -> None:
        """
        Call repository operations with default repository manager setup

        No special database configuration required for apk
        """
        pass

    def runtime_config(self) -> Dict:
        """
        apk runtime configuration and environment
        """
        return {
            'bootstrap_repo': self.bootstrap_repo,
            'command_env': self.command_env,
        }

    def add_repo(
        self, name: str, uri: str, repo_type: str = 'apk',
        prio: int = None, dist: str = None, components: str = None,
        user: str = None, secret: str = None, credentials_file: str = None,
        repo_gpgcheck: bool = None, pkg_gpgcheck: bool = None,
        sourcetype: str = None, customization_script: str = None,
        architectures: str = None
    ) -> None:
        """
        Add apk repository

        :param str name: repository name
        :param str uri: repository URI
        :param str repo_type: unused
        :param int prio: unused
        :param str dist: unused
        :param str components: unused
        :param str user: unused
        :param str secret: unused
        :param str credentials_file: unused
        :param bool repo_gpgcheck: unused
        :param bool pkg_gpgcheck: unused
        :param str sourcetype: unused
        :param str customization_script: unused
        :param str architectures: unused
        """
        self.repo_dict[name] = uri
        if not self.bootstrap_repo:
            # The first repo added is used for bootstrap
            self.bootstrap_repo = uri
        with open(self.repo_config, 'a') as repos:
            repos.write(f'{uri}{os.linesep}')

    def import_trusted_keys(self, signing_keys: List) -> None:
        """
        Imports trusted keys into the image

        :param list signing_keys: list of the key files to import
        """
        pass

    def delete_repo(self, name: str) -> None:
        """
        Delete apk repository

        :param str name: repository base file name
        """
        if self.repo_dict.get(name):
            self.delete_all_repos()
            del self.repo_dict[name]
            for name in self.repo_dict:
                self.add_repo(name, self.repo_dict[name])

    def delete_all_repos(self) -> None:
        """
        Delete all apk repositories
        """
        if os.path.isfile(self.repo_config):
            os.unlink(self.repo_config)

    def delete_repo_cache(self, name: str) -> None:
        """
        Delete repository cache

        No special cache cleanup required for apk

        :param str name: unused
        """
        pass

    def cleanup_unused_repos(self) -> None:
        """
        Cleanup/Delete unused repositories

        No special cleanup required for apk
        """
        pass

    def _create_apk_get_runtime_environment(self) -> Dict:
        return dict(
            os.environ, LANG='C'
        )
