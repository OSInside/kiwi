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
import os
from ConfigParser import ConfigParser
from tempfile import NamedTemporaryFile

# project
from repository_base import RepositoryBase
from path import Path

from exceptions import (
    KiwiRepoTypeUnknown
)


class RepositoryYum(RepositoryBase):
    """
        Implements repo handling for yum package manager
    """
    def post_init(self, custom_args=None):
        self.custom_args = custom_args
        if not custom_args:
            self.custom_args = []

        self.repo_names = []

        # yum support is based on creating repo files which contains
        # path names to the repo and its cache. In order to allow a
        # persistent use of the files in and outside of a chroot call
        # an active bind mount from RootBind::mount_shared_directory
        # is expected and required
        manager_base = self.shared_location

        self.shared_yum_dir = {
            'reposd-dir': manager_base + '/yum/repos',
            'cache-dir': manager_base + '/yum/cache'
        }

        self.runtime_yum_config_file = NamedTemporaryFile(
            dir=self.root_dir
        )

        self.yum_args = [
            '-c', self.runtime_yum_config_file.name, '-y'
        ] + self.custom_args

        self.command_env = self.__create_yum_runtime_environment()

        # config file parameters for yum tool
        self.runtime_yum_config = ConfigParser()
        self.runtime_yum_config.add_section('main')

        self.runtime_yum_config.set(
            'main', 'cachedir', self.shared_yum_dir['cache-dir']
        )
        self.runtime_yum_config.set(
            'main', 'reposdir', self.shared_yum_dir['reposd-dir']
        )
        self.runtime_yum_config.set(
            'main', 'keepcache', '0'
        )
        self.runtime_yum_config.set(
            'main', 'debuglevel', '2'
        )
        self.runtime_yum_config.set(
            'main', 'pkgpolicy', 'newest'
        )
        self.runtime_yum_config.set(
            'main', 'tolerant', '0'
        )
        self.runtime_yum_config.set(
            'main', 'exactarch', '1'
        )
        self.runtime_yum_config.set(
            'main', 'obsoletes', '1'
        )
        self.runtime_yum_config.set(
            'main', 'plugins', '1'
        )
        self.runtime_yum_config.set(
            'main', 'metadata_expire', '1800'
        )
        self.runtime_yum_config.set(
            'main', 'group_command', 'compat'
        )

        self.__write_runtime_config()

    def runtime_config(self):
        return {
            'yum_args': self.yum_args,
            'command_env': self.command_env
        }

    def add_repo(self, name, uri, repo_type='rpm-md', prio=None):
        repo_file = self.shared_yum_dir['reposd-dir'] + '/' + name + '.repo'
        self.repo_names.append(name + '.repo')
        if 'iso-mount' in uri:
            # iso mount point is a tmpdir, thus different each time we build
            Path.wipe(repo_file)
        if os.path.exists(uri):
            # yum requires local paths to take the file: type
            uri = 'file://' + uri
        if not os.path.exists(repo_file):
            repo_config = ConfigParser()
            repo_config.add_section(name)
            repo_config.set(
                name, 'name', name
            )
            repo_config.set(
                name, 'baseurl', uri
            )
            if prio:
                repo_config.set(
                    name, 'priority', format(prio)
                )
            with open(repo_file, 'w') as repo:
                repo_config.write(repo)

    def delete_repo(self, name):
        Path.wipe(
            self.shared_yum_dir['reposd-dir'] + '/' + name + '.repo'
        )

    def delete_all_repos(self):
        Path.wipe(self.shared_yum_dir['reposd-dir'])
        Path.create(self.shared_yum_dir['reposd-dir'])

    def cleanup_unused_repos(self):
        # repository configurations which are not used for this build
        # must be removed otherwise they are taken into account for
        # the package installations
        repos_dir = self.shared_yum_dir['reposd-dir']
        for elements in os.walk(repos_dir):
            for repo_file in list(elements[2]):
                if repo_file not in self.repo_names:
                    Path.wipe(repos_dir + '/' + repo_file)
            break

    def __create_yum_runtime_environment(self):
        for yum_dir in self.shared_yum_dir.values():
            Path.create(yum_dir)
        return dict(
            os.environ, LANG='C'
        )

    def __write_runtime_config(self):
        with open(self.runtime_yum_config_file.name, 'w') as config:
            self.runtime_yum_config.write(config)
