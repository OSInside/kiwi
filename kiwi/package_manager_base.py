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
        Implements base class for package manager install tasks
    """
    def __init__(self, repository, custom_args=None):
        self.repository = repository
        self.root_dir = repository.root_dir
        self.root_bind = repository.root_bind
        self.package_requests = []
        self.collection_requests = []
        self.product_requests = []

        self.post_init(custom_args)

    def post_init(self, custom_args=None):
        pass

    def request_package(self, name):
        raise NotImplementedError

    def request_collection(self, name):
        raise NotImplementedError

    def request_product(self, name):
        raise NotImplementedError

    def process_install_requests_bootstrap(self):
        raise NotImplementedError

    def process_install_requests(self):
        raise NotImplementedError

    def process_delete_requests(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def process_only_required(self):
        raise NotImplementedError

    def match_package_installed(self, package_list, log_line):
        raise NotImplementedError

    def match_package_deleted(self, package_list, log_line):
        raise NotImplementedError

    def database_consistent(self):
        raise NotImplementedError

    def dump_reload_package_database(self):
        raise NotImplementedError

    def cleanup_requests(self):
        del self.package_requests[:]
        del self.collection_requests[:]
        del self.product_requests[:]
