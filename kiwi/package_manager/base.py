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

from kiwi.api_helper import decommissioned
from kiwi.command import CommandCallT
from kiwi.system.root_bind import RootBind
from kiwi.repository.base import RepositoryBase


class PackageManagerBase:
    """
    **Implements base class for Package Management**

    :param object repository: instance of :class:`Repository`
    :param str root_dir: root directory path name
    :param list package_requests: list of packages to install or delete
    :param list collection_requests: list of collections to install
    :param list product_requests: list of products to install
    """
    def __init__(
        self, repository: RepositoryBase, custom_args: List = [],
        release_version: str = ''
    ) -> None:
        self.repository = repository
        self.root_dir = repository.root_dir
        self.package_requests: List[str] = []
        self.collection_requests: List[str] = []
        self.product_requests: List[str] = []
        self.exclude_requests: List[str] = []
        self.release_version = release_version or '0'

        self.post_init(custom_args or [])

    def __enter__(self):
        return self

    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Implementation in specialized package manager class

        :param list custom_args: unused
        """
        pass

    def request_package(self, name: str) -> None:
        """
        Queue a package request

        Implementation in specialized package manager class

        :param str name: unused
        """
        raise NotImplementedError

    def request_collection(self, name: str) -> None:
        """
        Queue a package collection

        Implementation in specialized package manager class

        :param str name: unused
        """
        raise NotImplementedError

    def request_product(self, name: str) -> None:
        """
        Queue a product request

        Implementation in specialized package manager class

        :param str name: unused
        """
        raise NotImplementedError

    @decommissioned
    def request_package_lock(self, name: str) -> None:
        pass  # pragma: no cover

    def request_package_exclusion(self, name: str) -> None:
        """
        Queue a package exclusion(skip) request

        Implementation in specialized package manager class

        :param str name: unused
        """
        raise NotImplementedError

    def setup_repository_modules(
        self, collection_modules: Dict[str, List[str]]
    ) -> None:
        """
        Setup repository modules and streams

        Implementation in specialized package manager class

        :param dict collection_modules: unused
        """
        raise NotImplementedError

    def process_install_requests_bootstrap(
        self, root_bind: RootBind = None, bootstrap_package: str = None
    ) -> CommandCallT:
        """
        Process package install requests for bootstrap phase (no chroot)

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def process_install_requests(self) -> CommandCallT:
        """
        Process package install requests for image phase (chroot)

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def process_delete_requests(self, force: bool = False) -> CommandCallT:
        """
        Process package delete requests (chroot)

        Implementation in specialized package manager class

        :param bool force: unused
        """
        raise NotImplementedError

    def update(self) -> CommandCallT:
        """
        Process package update requests (chroot)

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def process_only_required(self) -> None:
        """
        Setup package processing only for required packages

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def process_plus_recommended(self) -> None:
        """
        Setup package processing to also include recommended dependencies

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def match_package_installed(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        """
        Match expression to indicate a package has been installed

        Implementation in specialized package manager class

        :param str package_name: unused
        :param str package_manager_output: unused

        :return: True|False

        :rtype: bool
        """
        raise NotImplementedError

    def match_package_deleted(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        """
        Match expression to indicate a package has been deleted

        Implementation in specialized package manager class

        :param str package_name: unused
        :param str package_manager_output: unused

        :return: True|False

        :rtype: bool
        """
        raise NotImplementedError

    @decommissioned
    def database_consistent(self) -> None:
        pass  # pragma: no cover

    @decommissioned
    def dump_reload_package_database(self, version: int = 45) -> None:
        pass  # pragma: no cover

    def post_process_install_requests_bootstrap(
        self, root_bind: RootBind = None, delta_root: bool = False
    ) -> None:
        """
        Process extra code required after bootstrapping

        Implementation in specialized package manager class
        """
        pass

    def post_process_delete_requests(
        self, root_bind: RootBind = None
    ) -> None:
        """
        Process extra code required after deleting packages

        Implementation in specialized package manager class
        """
        pass

    @staticmethod
    def has_failed(returncode: int) -> bool:
        """
        Evaluate given result return code

        Any returncode != 0 is considered an error unless
        overwritten in specialized package manager class

        :param int returncode: return code number

        :return: True|False

        :rtype: boolean
        """
        return returncode != 0

    def get_error_details(self) -> str:
        """
        Provide further error details

        In case the package manager call failed this
        method will return package manager specific error
        information if there is any

        :return: further error data as str or empty str

        :rtype: str
        """
        return ''

    def clean_leftovers(self) -> None:
        """
        Cleans package manager related data not needed in the
        resulting image such as custom macros

        Implementation in specialized package manager class
        """
        pass

    def cleanup_requests(self) -> None:
        """
        Cleanup request queues
        """
        del self.package_requests[:]
        del self.collection_requests[:]
        del self.product_requests[:]
        del self.exclude_requests[:]

    def __exit__(self, exc_type, exc_value, traceback):
        if self.repository:
            self.repository.cleanup()
