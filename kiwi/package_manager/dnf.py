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
from kiwi.command import CommandCallT
from kiwi.package_manager.base import PackageManagerBase
from kiwi.system.root_bind import RootBind
from kiwi.api_helper import decommissioned


class PackageManagerDnf(PackageManagerBase):
    """
    decommissioned, moved to PackageManagerDnf4
    """
    @decommissioned
    def post_init(self, custom_args: List = []) -> None:
        pass  # pragma: no cover

    @decommissioned
    def request_package(self, name: str) -> None:
        pass  # pragma: no cover

    @decommissioned
    def request_collection(self, name: str) -> None:
        pass  # pragma: no cover

    @decommissioned
    def request_product(self, name: str) -> None:
        pass  # pragma: no cover

    @decommissioned
    def request_package_exclusion(self, name: str) -> None:
        pass  # pragma: no cover

    @decommissioned
    def setup_repository_modules(
        self, collection_modules: Dict[str, List[str]]
    ) -> None:
        pass  # pragma: no cover

    @no_type_check
    @decommissioned
    def process_install_requests_bootstrap(
        self, root_bind: RootBind = None, bootstrap_package: str = None
    ) -> CommandCallT:
        pass  # pragma: no cover

    @no_type_check
    @decommissioned
    def process_install_requests(self) -> CommandCallT:
        pass  # pragma: no cover

    @no_type_check
    @decommissioned
    def process_delete_requests(self, force: bool = False) -> CommandCallT:
        pass  # pragma: no cover

    @no_type_check
    @decommissioned
    def update(self) -> CommandCallT:
        pass  # pragma: no cover

    @decommissioned
    def process_only_required(self) -> None:
        pass  # pragma: no cover

    @decommissioned
    def process_plus_recommended(self) -> None:
        pass  # pragma: no cover

    @no_type_check
    @decommissioned
    def match_package_installed(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        pass  # pragma: no cover

    @no_type_check
    @decommissioned
    def match_package_deleted(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        pass  # pragma: no cover

    @decommissioned
    def post_process_install_requests_bootstrap(
        self, root_bind: RootBind = None, delta_root: bool = False
    ) -> None:
        pass  # pragma: no cover

    @decommissioned
    def clean_leftovers(self) -> None:
        pass  # pragma: no cover
