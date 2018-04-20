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


class RepositoryBase(object):
    """
    Implements base class for package manager repository handling

    Attributes

    :param object root_bind: instance of :class:`RootBind`
    :param str root_dir: root directory path name
    :param str shared_location: shared directory between image root
        and build system root
    """
    def __init__(self, root_bind, custom_args=None):
        self.root_bind = root_bind
        self.root_dir = root_bind.root_dir
        self.shared_location = root_bind.shared_location

        self.post_init(custom_args)

    def post_init(self, custom_args):
        """
        Post initialization method

        Implementation in specialized repository class

        :param list custom_args: unused
        """
        pass

    def use_default_location(self):
        """
        Call repository operations with default repository manager setup

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def runtime_config(self):
        """
        Repository runtime configuration and environment

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def add_repo(
        self, name, uri, repo_type, prio, dist, components,
        user, secret, credentials_file, repo_gpgcheck, pkg_gpgcheck
    ):
        """
        Add repository

        Implementation in specialized repository class

        :param str name: unused
        :param str uri: unused
        :param repo_type: unused
        :param int prio: unused
        :param dist: unused
        :param components: unused
        :param user: unused
        :param secret: unused
        :param credentials_file: unused
        :param repo_gpgcheck: unused
        :param pkg_gpgcheck: unused
        """
        raise NotImplementedError

    def import_trusted_keys(self, signing_keys):
        """
        Imports trusted keys into the image

        Implementation in specialized repository class

        :param list signing_keys: list of the key files to import
        """
        raise NotImplementedError

    def cleanup_unused_repos(self):
        """
        Cleanup/Delete unused repositories

        Only configured repositories according to the image configuration
        are allowed to be active when building

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def delete_repo(self, name):
        """
        Delete repository

        Implementation in specialized repository class

        :param str name: unused
        """
        raise NotImplementedError

    def delete_all_repos(self):
        """
        Delete all repositories

        Implementation in specialized repository class
        """
        raise NotImplementedError

    def delete_repo_cache(self, name):
        """
        Delete repository cache

        Implementation in specialized repository class

        :param str name: unused
        """
        raise NotImplementedError
