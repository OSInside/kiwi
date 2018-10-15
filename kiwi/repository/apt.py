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
from tempfile import NamedTemporaryFile
from six.moves.urllib.parse import urlparse

# project
from kiwi.repository.template.apt import PackageManagerTemplateAptGet
from kiwi.repository.base import RepositoryBase
from kiwi.path import Path


class RepositoryApt(RepositoryBase):
    """
    **Implements repository handling for apt-get package manager**

    :param str shared_apt_get_dir: shared directory between image root and build system root
    :param str runtime_apt_get_config_file: apt-get runtime config file name
    :param list apt_get_args: apt-get caller arguments
    :param dict command_env: customized os.environ for apt-get
    :param manager_base: shared location for apt-get repodata between
        host and image
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom apt-get arguments and create runtime configuration
        and environment

        :param list custom_args: apt-get arguments
        """
        self.custom_args = custom_args
        self.exclude_docs = False
        self.signing_keys = []
        if not custom_args:
            self.custom_args = []

        # extract custom arguments used for apt config only
        if 'exclude_docs' in self.custom_args:
            self.custom_args.remove('exclude_docs')
            self.exclude_docs = True

        if 'check_signatures' in self.custom_args:
            self.custom_args.remove('check_signatures')
            self.unauthenticated = 'false'
        else:
            self.unauthenticated = 'true'

        self.distribution = None
        self.distribution_path = None
        self.repo_names = []

        # apt-get support is based on creating a sources file which
        # contains path names to the repo and its cache. In order to
        # allow a persistent use of the files in and outside of a chroot
        # call an active bind mount from RootBind::mount_shared_directory
        # is expected and required
        self.manager_base = self.shared_location + '/apt-get'

        self.shared_apt_get_dir = {
            'sources-dir': self.manager_base + '/sources.list.d',
            'preferences-dir': self.manager_base + '/preferences.d'
        }

        self.runtime_apt_get_config_file = NamedTemporaryFile(
            dir=self.root_dir
        )

        self.apt_get_args = [
            '-q', '-c', self.runtime_apt_get_config_file.name, '-y'
        ] + self.custom_args

        self.command_env = self._create_apt_get_runtime_environment()

        # config file for apt-get tool
        self.apt_conf = PackageManagerTemplateAptGet()
        self._write_runtime_config()

    def use_default_location(self):
        """
        Setup apt-get repository operations to store all data
        in the default places
        """
        self.manager_base = os.sep.join([self.root_dir, 'etc/apt'])
        self.shared_apt_get_dir['sources-dir'] = \
            os.sep.join([self.manager_base, 'sources.list.d'])
        self.shared_apt_get_dir['preferences-dir'] = \
            os.sep.join([self.root_dir, 'preferences.d'])
        self._write_runtime_config(system_default=True)

    def runtime_config(self):
        """
        apt-get runtime configuration and environment
        """
        return {
            'apt_get_args': self.apt_get_args,
            'command_env': self.command_env,
            'distribution': self.distribution,
            'distribution_path': self.distribution_path
        }

    def add_repo(
        self, name, uri, repo_type='deb',
        prio=None, dist=None, components=None,
        user=None, secret=None, credentials_file=None,
        repo_gpgcheck=None, pkg_gpgcheck=None
    ):
        """
        Add apt_get repository

        :param str name: repository base file name
        :param str uri: repository URI
        :param repo_type: unused
        :param int prio: unused
        :param dist: distribution name for non flat deb repos
        :param components: distribution categories
        :param user: unused
        :param secret: unused
        :param credentials_file: unused
        :param bool repo_gpgcheck: enable repository signature validation
        :param pkg_gpgcheck: unused
        """
        list_file = '/'.join(
            [self.shared_apt_get_dir['sources-dir'], name + '.list']
        )
        pref_file = '/'.join(
            [self.shared_apt_get_dir['preferences-dir'], name + '.pref']
        )
        self.repo_names.append(name + '.list')
        if os.path.exists(uri):
            # apt-get requires local paths to take the file: type
            uri = 'file:/' + uri
            uri = uri.replace('file://', 'file:/')
        if not components:
            components = 'main'
        with open(list_file, 'w') as repo:
            if repo_gpgcheck is None:
                repo_line = 'deb {0}'.format(uri)
            else:
                repo_line = 'deb [trusted={0}] {1}'.format(
                    'no' if repo_gpgcheck else 'yes', uri
                )
            if not dist:
                # create a debian flat repository setup. We consider the
                # repository metadata to exist on the toplevel of the
                # specified uri. This applies to the way the open build
                # service creates debian repositories and should be
                # done in the same way for other repositories when used
                # with kiwi
                repo_line += ' ./\n'
            else:
                # create a debian distributon repository setup for the
                # specified distributon name and components
                self.distribution = dist
                self.distribution_path = uri
                repo_line += ' {0} {1}\n'.format(dist, components)
            repo.write(repo_line)
        if prio:
            uri_parsed = urlparse(uri.replace('file://', 'file:/'))
            with open(pref_file, 'w') as pref:
                pref.write('Package: *{0}'.format(os.linesep))
                if not uri_parsed.hostname:
                    pref.write(
                        'Pin: origin ""{0}'.format(os.linesep)
                    )
                else:
                    pref.write(
                        'Pin: origin "{0}"{1}'.format(
                            uri_parsed.hostname, os.linesep
                        )
                    )
                pref.write(
                    'Pin-Priority: {0}{1}'.format(prio, os.linesep)
                )

    def import_trusted_keys(self, signing_keys):
        """
        Keeps trusted keys so that later on they can be imported into
        the image by the PackageManager instance.

        :param list signing_keys: list of the key files to import
        """
        for key in signing_keys:
            self.signing_keys.append(key)

    def delete_repo(self, name):
        """
        Delete apt-get repository

        :param str name: repository base file name
        """
        Path.wipe(
            self.shared_apt_get_dir['sources-dir'] + '/' + name + '.list'
        )

    def delete_all_repos(self):
        """
        Delete all apt-get repositories
        """
        Path.wipe(self.shared_apt_get_dir['sources-dir'])
        Path.create(self.shared_apt_get_dir['sources-dir'])

    def delete_repo_cache(self, name):
        """
        Delete apt-get repository cache

        Apt stores the package cache in a collection of binary files
        and deb archives. As of now I couldn't came across a solution
        which allows for deleting only the cache data for a specific
        repository. Thus the repo cache cleanup affects all cache
        data

        :param str name: unused
        """
        for cache_file in ['archives', 'pkgcache.bin', 'srcpkgcache.bin']:
            Path.wipe(os.sep.join([self.manager_base, cache_file]))

    def cleanup_unused_repos(self):
        """
        Delete unused apt_get repositories

        Repository configurations which are not used for this build
        must be removed otherwise they are taken into account for
        the package installations
        """
        repos_dir = self.shared_apt_get_dir['sources-dir']
        repo_files = list(os.walk(repos_dir))[0][2]
        for repo_file in repo_files:
            if repo_file not in self.repo_names:
                Path.wipe(repos_dir + '/' + repo_file)

    def _create_apt_get_runtime_environment(self):
        for apt_get_dir in list(self.shared_apt_get_dir.values()):
            Path.create(apt_get_dir)
        return dict(
            os.environ, LANG='C', DEBIAN_FRONTEND='noninteractive'
        )

    def _write_runtime_config(self, system_default=False):
        parameters = {
            'apt_shared_base': self.manager_base,
            'unauthenticated': self.unauthenticated
        }
        if not system_default:
            template = self.apt_conf.get_host_template(self.exclude_docs)
            apt_conf_data = template.substitute(parameters)
        else:
            template = self.apt_conf.get_image_template(self.exclude_docs)
            apt_conf_data = template.substitute(parameters)

        with open(self.runtime_apt_get_config_file.name, 'w') as config:
            config.write(apt_conf_data)
