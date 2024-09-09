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
from typing import (
    List, Dict
)

from kiwi.system.root_bind import RootBind
from kiwi.command import Command


class RepositoryBase:
    """
    Implements base class for package manager repository handling

    Attributes

    :param object root_bind: instance of :class:`RootBind`
    :param str root_dir: root directory path name
    :param str shared_location: shared directory between image root
        and build system root
    """

    def __init__(
        self, root_bind: RootBind, custom_args: List = []
    ) -> None:
        self.root_bind = root_bind
        self.root_dir = root_bind.root_dir
        self.shared_location = root_bind.shared_location

        self.post_init(custom_args or [])

    def __enter__(self):
        return self

    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Implementation in specialized repository class

        :param list custom_args: unused
        """
        pass

    def use_default_location(self) -> None:
        """
        Call repository operations with default repository manager setup

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def runtime_config(self) -> Dict:
        """
        Repository runtime configuration and environment

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def add_repo(
        self, name: str, uri: str, repo_type: str, prio: int, dist: str,
        components: str, user: str, secret: str, credentials_file: str,
        repo_gpgcheck: bool, pkg_gpgcheck: bool, sourcetype: str,
        customization_script: str = None, architectures: str = None
    ) -> None:
        """
        Add repository

        Implementation in specialized repository class

        :param str name: unused
        :param str uri: unused
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
        raise NotImplementedError

    def setup_package_database_configuration(self) -> None:
        """
        Setup package database configuration

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def import_trusted_keys(self, signing_keys: List) -> None:
        """
        Imports trusted keys into the image

        Implementation in specialized repository class

        :param list signing_keys: list of the key files to import
        """
        raise NotImplementedError

    def cleanup_unused_repos(self) -> None:
        """
        Cleanup/Delete unused repositories

        Only configured repositories according to the image configuration
        are allowed to be active when building

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def delete_repo(self, name: str) -> None:
        """
        Delete repository

        Implementation in specialized repository class

        :param str name: unused
        """
        raise NotImplementedError

    def delete_all_repos(self) -> None:
        """
        Delete all repositories

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def delete_repo_cache(self, name: str) -> None:
        """
        Delete repository cache

        Implementation in specialized repository class

        :param str name: unused
        """
        raise NotImplementedError

    @staticmethod
    def run_repo_customize(script_path: str, repo_file) -> None:
        """
        Run an optional customization script

        :param str script_path: unused
        :param str repo_file: unused
        """
        Command.run(
            ['bash', '--norc', script_path, repo_file]
        )

    def cleanup(self) -> None:
        """
        Cleanup method

        Implementation in specialized repository class
        """
        pass  # pragma: no cover

    def __exit__(self, exc_type, exc_value, traceback):
        pass  # pragma: no cover
