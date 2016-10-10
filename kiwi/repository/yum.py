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
from six.moves.configparser import ConfigParser
from tempfile import NamedTemporaryFile

# project
from ..logger import log
from .base import RepositoryBase
from ..path import Path


class RepositoryYum(RepositoryBase):
    """
    Implements repository handling for yum package manager
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom yum arguments and create runtime configuration
        and environment

        Attributes

        * :attr:`shared_yum_dir`
            shared directory between image root and build system root

        * :attr:`runtime_yum_config_file`
            yum runtime config file name

        * :attr:`command_env`
            customized os.environ for yum

        * :attr:`runtime_yum_config`
            Instance of ConfigParser

        :param list custom_args: yum arguments
        """
        self.custom_args = custom_args
        if not custom_args:
            self.custom_args = []

        # extract custom arguments not used in yum call
        if 'exclude_docs' in self.custom_args:
            self.custom_args.remove('exclude_docs')
            log.warning('rpm-excludedocs not supported for yum: ignoring')

        self.repo_names = []

        # yum support is based on creating repo files which contains
        # path names to the repo and its cache. In order to allow a
        # persistent use of the files in and outside of a chroot call
        # an active bind mount from RootBind::mount_shared_directory
        # is expected and required
        manager_base = self.shared_location + '/yum'

        self.shared_yum_dir = {
            'reposd-dir': manager_base + '/repos',
            'cache-dir': manager_base + '/cache',
            'pluginconf-dir': manager_base + '/pluginconf'
        }

        self.runtime_yum_config_file = NamedTemporaryFile(
            dir=self.root_dir
        )

        self.yum_args = [
            '-c', self.runtime_yum_config_file.name, '-y'
        ] + self.custom_args

        self.command_env = self._create_yum_runtime_environment()

        # config file parameters for yum tool
        self._create_runtime_config_parser()
        self._create_runtime_plugin_config_parser()
        self._write_runtime_config()

    def use_default_location(self):
        """
        Setup yum repository operations to store all data
        in the default places
        """
        self.shared_yum_dir['reposd-dir'] = \
            self.root_dir + '/etc/yum/repos.d'
        self.shared_yum_dir['cache-dir'] = \
            self.root_dir + '/var/cache/yum'
        self.shared_yum_dir['pluginconf-dir'] = \
            self.root_dir + '/etc/yum/pluginconf.d'
        self._create_runtime_config_parser()
        self._create_runtime_plugin_config_parser()
        self._write_runtime_config()

    def runtime_config(self):
        """
        yum runtime configuration and environment
        """
        return {
            'yum_args': self.yum_args,
            'command_env': self.command_env
        }

    def add_repo(
        self, name, uri, repo_type='rpm-md', prio=None, dist=None, components=None
    ):
        """
        Add yum repository

        :param string name: repository base file name
        :param string uri: repository URI
        :param repo_type: repostory type name
        :param int prio: yum repostory priority
        :param dist: unused
        :param components: unused
        """
        repo_file = self.shared_yum_dir['reposd-dir'] + '/' + name + '.repo'
        self.repo_names.append(name + '.repo')
        if os.path.exists(uri):
            # yum requires local paths to take the file: type
            uri = 'file://' + uri
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
        """
        Delete yum repository

        :param string name: repository base file name
        """
        Path.wipe(
            self.shared_yum_dir['reposd-dir'] + '/' + name + '.repo'
        )

    def delete_all_repos(self):
        """
        Delete all yum repositories
        """
        Path.wipe(self.shared_yum_dir['reposd-dir'])
        Path.create(self.shared_yum_dir['reposd-dir'])

    def cleanup_unused_repos(self):
        """
        Delete unused yum repositories

        Repository configurations which are not used for this build
        must be removed otherwise they are taken into account for
        the package installations
        """
        repos_dir = self.shared_yum_dir['reposd-dir']
        repo_files = list(os.walk(repos_dir))[0][2]
        for repo_file in repo_files:
            if repo_file not in self.repo_names:
                Path.wipe(repos_dir + '/' + repo_file)

    def _create_yum_runtime_environment(self):
        for yum_dir in list(self.shared_yum_dir.values()):
            Path.create(yum_dir)
        return dict(
            os.environ, LANG='C'
        )

    def _create_runtime_config_parser(self):
        self.runtime_yum_config = ConfigParser()
        self.runtime_yum_config.add_section('main')

        self.runtime_yum_config.set(
            'main', 'cachedir', self.shared_yum_dir['cache-dir']
        )
        self.runtime_yum_config.set(
            'main', 'reposdir', self.shared_yum_dir['reposd-dir']
        )
        self.runtime_yum_config.set(
            'main', 'pluginconfpath', self.shared_yum_dir['pluginconf-dir']
        )
        self.runtime_yum_config.set(
            'main', 'keepcache', '1'
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

    def _create_runtime_plugin_config_parser(self):
        self.runtime_yum_plugin_config = ConfigParser()
        self.runtime_yum_plugin_config.add_section('main')

        self.runtime_yum_plugin_config.set(
            'main', 'enabled', '1'
        )

    def _write_runtime_config(self):
        with open(self.runtime_yum_config_file.name, 'w') as config:
            self.runtime_yum_config.write(config)
        yum_plugin_config_file = \
            self.shared_yum_dir['pluginconf-dir'] + '/priorities.conf'
        with open(yum_plugin_config_file, 'w') as pluginconfig:
            self.runtime_yum_plugin_config.write(pluginconfig)
