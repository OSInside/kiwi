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
        Implements base class for package manager repo handling
    """
    def __init__(self, root_bind, custom_args=None):
        self.root_bind = root_bind
        self.root_dir = root_bind.root_dir
        self.shared_location = root_bind.shared_location

        self.post_init(custom_args)

    def post_init(self, custom_args):
        pass

    def runtime_config(self):
        raise NotImplementedError

    def add_repo(self, name, uri, repo_type, prio):
        raise NotImplementedError

    def cleanup_unused_repos(self):
        raise NotImplementedError

    def delete_repo(self, name):
        raise NotImplementedError

    def delete_all_repos(self):
        raise NotImplementedError
