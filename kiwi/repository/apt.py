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
import logging
from urllib.parse import urlparse
from typing import List, Dict

# project
from kiwi.utils.temporary import (
    Temporary, TmpT
)
from kiwi.repository.template.apt import PackageManagerTemplateAptGet
from kiwi.repository.base import RepositoryBase
from kiwi.path import Path
from kiwi.command import Command

log = logging.getLogger('kiwi')


class RepositoryApt(RepositoryBase):
    """
    **Implements repository handling for apt-get package manager**

    :param str shared_apt_get_dir:
        shared directory between image root and build system root
    :param str runtime_apt_get_config_file: apt-get runtime config file name
    :param list apt_get_args: apt-get caller arguments
    :param dict command_env: customized os.environ for apt-get
    :param manager_base: shared location for apt-get repodata between
        host and image
    """

    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Store custom apt-get arguments and create runtime configuration
        and environment

        :param list custom_args: apt-get arguments
        """
        self.runtime_apt_get_config_file = TmpT(name='')
        self.custom_args = custom_args
        self.exclude_docs = False
        self.signing_keys: List = []

        # extract custom arguments used for apt config only
        if 'exclude_docs' in self.custom_args:
            self.custom_args.remove('exclude_docs')
            self.exclude_docs = True

        if 'check_signatures' in self.custom_args:
            self.custom_args.remove('check_signatures')
            self.unauthenticated = 'false'
        else:
            self.unauthenticated = 'true'

        self.distribution: str = ''
        self.distribution_path: str = ''
        self.repo_names: List = []
        self.components: List = []

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
        self.keyring = '{}/trusted.gpg'.format(self.manager_base)

        self.runtime_apt_get_config_file = Temporary(
            path=self.root_dir, prefix='kiwi_apt.conf'
        ).unmanaged_file()

        self.apt_get_args = [
            '-q', '-c', self.runtime_apt_get_config_file.name, '-y'
        ] + self.custom_args

        self.command_env = self._create_apt_get_runtime_environment()

        # config file for apt-get tool
        self.apt_conf = PackageManagerTemplateAptGet()
        self._write_runtime_config()

    def setup_package_database_configuration(self) -> None:
        """
        Setup package database configuration

        No special database configuration required for apt
        """
        pass

    def use_default_location(self) -> None:
        """
        Setup apt-get repository operations to store all data
        in the default places
        """
        self.manager_base = os.sep.join([self.root_dir, 'etc/apt'])
        self.shared_apt_get_dir['sources-dir'] = \
            os.sep.join([self.manager_base, 'sources.list.d'])
        self.shared_apt_get_dir['preferences-dir'] = \
            os.sep.join([self.manager_base, 'preferences.d'])
        self._write_runtime_config(system_default=True)

    def runtime_config(self) -> Dict:
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
        self, name: str, uri: str, repo_type: str = 'deb',
        prio: int = None, dist: str = None, components: str = None,
        user: str = None, secret: str = None, credentials_file: str = None,
        repo_gpgcheck: bool = None, pkg_gpgcheck: bool = None,
        sourcetype: str = None, customization_script: str = None,
        architectures: str = None
    ) -> None:
        """
        Add apt_get repository

        :param str name: repository base file name
        :param str uri: repository URI
        :param str repo_type: unused
        :param int prio: unused
        :param str dist: distribution name for non flat deb repos
        :param str components: distribution categories
        :param str user: unused
        :param str secret: unused
        :param str credentials_file: unused
        :param bool repo_gpgcheck: enable repository signature validation
        :param bool pkg_gpgcheck: unused
        :param str sourcetype: unused
        :param str customization_script:
            custom script called after the repo file was created
        :param str architectures:
            identifies which architectures are supported by this repository
        """
        sources_file = '/'.join(
            [self.shared_apt_get_dir['sources-dir'], name + '.sources']
        )
        pref_file = '/'.join(
            [self.shared_apt_get_dir['preferences-dir'], name + '.pref']
        )
        self.repo_names.append(name + '.sources')
        if os.path.exists(uri):
            # apt-get requires local paths to take the file: type
            uri = 'file:/' + uri
            uri = uri.replace('file://', 'file:/')
        if not components:
            components = 'main'
        self._add_components(components)
        with open(sources_file, 'w') as repo:
            repo_details = 'Types: deb' + os.linesep
            repo_details += 'URIs: ' + uri + os.linesep
            if architectures:
                repo_details += 'Architectures: {}{}'.format(
                    architectures.replace(',', ' '), os.linesep
                )
            if not dist:
                # create a debian flat repository setup. We consider the
                # repository metadata to exist on the toplevel of the
                # specified uri. This applies to the way the open build
                # service creates debian repositories and should be
                # done in the same way for other repositories when used
                # with kiwi
                repo_details += 'Suites: ./' + os.linesep
            else:
                # create a debian distributon repository setup for the
                # specified distributon name and components
                self.distribution = dist
                self.distribution_path = uri
                repo_details += 'Suites: ' + dist + os.linesep
                repo_details += 'Components: ' + components + os.linesep
            if repo_gpgcheck is False:
                repo_details += 'trusted: yes' + os.linesep
                repo_details += 'check-valid-until: no' + os.linesep
            repo.write(repo_details)
        if customization_script:
            self.run_repo_customize(customization_script, sources_file)
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
            if customization_script:
                self.run_repo_customize(customization_script, pref_file)

    def import_trusted_keys(self, signing_keys: List) -> None:
        """
        Creates a new keyring including provided keys

        :param list signing_keys: list of the key files to import
        """
        keybox = '{}/trusted-keybox.gpg'.format(self.manager_base)
        gpg_args = [
            'gpg', '--no-options', '--no-default-keyring',
            '--no-auto-check-trustdb', '--trust-model', 'always',
            '--keyring', keybox
        ]
        if os.path.exists(self.keyring):
            os.unlink(self.keyring)
        if os.path.exists(keybox):
            os.unlink(keybox)
        for key in signing_keys:
            Command.run(gpg_args + ['--import', '--ignore-time-conflict', key])
        if os.path.exists(keybox):
            Command.run(
                gpg_args + ['--export', '--yes', '--output', self.keyring]
            )
            os.unlink(keybox)
            log.info('Custom keyring for APT created: {}'.format(self.keyring))
            log.warning(
                'The keyring is only available at build time. '
                'It will not be part of the resulting image'
            )

    def delete_repo(self, name: str) -> None:
        """
        Delete apt-get repository

        :param str name: repository base file name
        """
        Path.wipe(
            self.shared_apt_get_dir['sources-dir'] + '/' + name + '.sources'
        )

    def delete_all_repos(self) -> None:
        """
        Delete all apt-get repositories
        """
        Path.wipe(self.shared_apt_get_dir['sources-dir'])
        Path.create(self.shared_apt_get_dir['sources-dir'])

    def delete_repo_cache(self, name: str) -> None:
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

    def cleanup_unused_repos(self) -> None:
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

    def _add_components(self, components: str) -> None:
        for component in components.split():
            if component not in self.components:
                self.components.append(component)

    def _create_apt_get_runtime_environment(self) -> Dict:
        for apt_get_dir in list(self.shared_apt_get_dir.values()):
            Path.create(apt_get_dir)
        return dict(
            os.environ, LANG='C', DEBIAN_FRONTEND='noninteractive'
        )

    def _write_runtime_config(self, system_default: bool = False) -> None:
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

    def cleanup(self) -> None:
        """
        Delete intermediate apt config file
        """
        if os.path.isfile(self.runtime_apt_get_config_file.name):
            os.unlink(self.runtime_apt_get_config_file.name)
