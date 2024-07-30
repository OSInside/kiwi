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
    List, Dict, no_type_check
)

# project
from kiwi.repository.base import RepositoryBase
from kiwi.api_helper import decommissioned


class RepositoryDnf(RepositoryBase):
    """
    decommissioned
    """
    @decommissioned
    def post_init(self, custom_args: List = []) -> None:
        pass  # pragma: no cover

    @decommissioned
    def setup_package_database_configuration(self) -> None:
        pass  # pragma: no cover

    @decommissioned
    def use_default_location(self) -> None:
        pass  # pragma: no cover

    @no_type_check
    @decommissioned
    def runtime_config(self) -> Dict:
        pass  # pragma: no cover

    @decommissioned
    def add_repo(
        self, name: str, uri: str, repo_type: str = 'rpm-md',
        prio: int = None, dist: str = None, components: str = None,
        user: str = None, secret: str = None, credentials_file: str = None,
        repo_gpgcheck: bool = False, pkg_gpgcheck: bool = False,
        sourcetype: str = None, customization_script: str = None
    ) -> None:
        pass  # pragma: no cover

    @decommissioned
    def import_trusted_keys(self, signing_keys: List) -> None:
        pass  # pragma: no cover

    @decommissioned
    def delete_repo(self, name: str) -> None:
        pass  # pragma: no cover

    @decommissioned
    def delete_all_repos(self) -> None:
        pass  # pragma: no cover

    @decommissioned
    def delete_repo_cache(self, name: str) -> None:
        pass  # pragma: no cover

    @decommissioned
    def cleanup_unused_repos(self) -> None:
        pass  # pragma: no cover

    @no_type_check
    @decommissioned
    def _create_dnf_runtime_environment(self) -> Dict:
        pass  # pragma: no cover

    @decommissioned
    def _create_runtime_config_parser(self) -> None:
        pass  # pragma: no cover

    @decommissioned
    def _create_runtime_plugin_config_parsers(self) -> None:
        pass  # pragma: no cover

    @decommissioned
    def _write_runtime_config(self) -> None:
        pass  # pragma: no cover
