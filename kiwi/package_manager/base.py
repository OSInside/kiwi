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


class PackageManagerBase(object):
    """
    **Implements base class for installation/deletion of
    packages and collections using a package manager**

    :param object repository: instance of :class:`Repository`
    :param str root_dir: root directory path name
    :param object root_bind: instance of :class:`RootBind`
    :param list package_requests: list of packages to install or delete
    :param list collection_requests: list of collections to install
    :param list product_requests: list of products to install
    """
    def __init__(self, repository, custom_args=None):
        self.repository = repository
        self.root_dir = repository.root_dir
        self.root_bind = repository.root_bind
        self.package_requests = []
        self.collection_requests = []
        self.product_requests = []
        self.exclude_requests = []

        self.post_init(custom_args)

    def post_init(self, custom_args=None):
        """
        Post initialization method

        Implementation in specialized package manager class

        :param list custom_args: unused
        """
        pass

    def request_package(self, name):
        """
        Queue a package request

        Implementation in specialized package manager class

        :param str name: unused
        """
        raise NotImplementedError

    def request_collection(self, name):
        """
        Queue a package collection

        Implementation in specialized package manager class

        :param str name: unused
        """
        raise NotImplementedError

    def request_product(self, name):
        """
        Queue a product request

        Implementation in specialized package manager class

        :param str name: unused
        """
        raise NotImplementedError

    def request_package_lock(self, name):
        """
        Queue a package exclusion(skip) request

        Obsolete method, only kept for API compatbility
        Method calls: request_package_exclusion
        """
        return self.request_package_exclusion(name)

    def request_package_exclusion(self, name):
        """
        Queue a package exclusion(skip) request

        Implementation in specialized package manager class

        :param str name: unused
        """
        raise NotImplementedError

    def process_install_requests_bootstrap(self):
        """
        Process package install requests for bootstrap phase (no chroot)

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def process_install_requests(self):
        """
        Process package install requests for image phase (chroot)

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def process_delete_requests(self, force=False):
        """
        Process package delete requests (chroot)

        Implementation in specialized package manager class

        :param bool force: unused
        """
        raise NotImplementedError

    def update(self):
        """
        Process package update requests (chroot)

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def process_only_required(self):
        """
        Setup package processing only for required packages

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def process_plus_recommended(self):
        """
        Setup package processing to also include recommended dependencies

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def match_package_installed(self, package_list, log_line):
        """
        Match expression to indicate a package has been installed

        Implementation in specialized package manager class

        :param list package_list: unused
        :param str log_line: unused
        """
        raise NotImplementedError

    def match_package_deleted(self, package_list, log_line):
        """
        Match expression to indicate a package has been deleted

        Implementation in specialized package manager class

        :param list package_list: unused
        :param str log_line: unused
        """
        raise NotImplementedError

    def database_consistent(self):
        """
        Check if package database is consistent

        Implementation in specialized package manager class
        """
        raise NotImplementedError

    def dump_reload_package_database(self, version=45):
        """
        For rpm based package managers, dump and reload the database
        to match the desired rpm db version

        Implementation in specialized package manager class

        :param str version: unused
        """
        raise NotImplementedError

    def cleanup_requests(self):
        """
        Cleanup request queues
        """
        del self.package_requests[:]
        del self.collection_requests[:]
        del self.product_requests[:]
        del self.exclude_requests[:]
