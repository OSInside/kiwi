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
from configparser import ConfigParser
from typing import List, Dict

# project
from kiwi.utils.temporary import Temporary
from kiwi.defaults import Defaults
from kiwi.command import Command
from kiwi.repository.base import RepositoryBase
from kiwi.system.uri import Uri
from kiwi.path import Path
from kiwi.utils.rpm_database import RpmDataBase


class RepositoryZypper(RepositoryBase):
    """
    **Implements repo handling for zypper package manager**

    :param str shared_zypper_dir: shared directory between image root
        and build system root
    :param str runtime_zypper_config_file: zypper runtime config file name
    :param str runtime_zypp_config_file: libzypp runtime config file name
    :param list zypper_args: zypper caller args plus additional custom args
    :param dict command_env: customized os.environ for zypper
    :param object runtime_zypper_config: instance of :class:`ConfigParser`
    """

    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Store custom zypper arguments and create runtime configuration
        and environment

        :param list custom_args: zypper arguments
        """
        self.custom_args = custom_args
        self.exclude_docs = False
        self.gpgcheck = False
        self.locale = None
        self.target_arch = None

        # extract custom arguments used for zypp config only
        if 'exclude_docs' in self.custom_args:
            self.custom_args.remove('exclude_docs')
            self.exclude_docs = True

        if 'check_signatures' in self.custom_args:
            self.custom_args.remove('check_signatures')
            self.gpgcheck = True

        for argument in self.custom_args:
            if '_install_langs' in argument:
                self.locale = argument
            elif '_target_arch' in argument:
                self.target_arch = argument
        if self.locale:
            self.custom_args.remove(self.locale)
        if self.target_arch:
            self.custom_args.remove(self.target_arch)
            self.target_arch = self.target_arch.split('%')[1]

        self.repo_names: List = []

        # zypper support by default point all actions into the root
        # directory of the image system. This information is passed
        # as arguments to zypper and adapted if the call runs as
        # chrooted operation. Therefore the use of the shared location
        # via RootBind::mount_shared_directory is optional but
        # recommended to make use of the repo cache
        manager_base = self.root_dir + self.shared_location

        self.shared_zypper_dir = {
            'pkg-cache-dir': os.sep.join(
                [manager_base, 'packages']
            ),
            'reposd-dir': os.sep.join(
                [manager_base, 'zypper/repos']
            ),
            'credentials-dir': os.sep.join(
                [manager_base, 'zypper/credentials']
            ),
            'solv-cache-dir': os.sep.join(
                [manager_base, 'zypper/solv']
            ),
            'raw-cache-dir': os.sep.join(
                [manager_base, 'zypper/raw']
            ),
            'cache-dir': os.sep.join(
                [manager_base, 'zypper']
            )
        }

        self.runtime_zypper_config_file = Temporary(
            dir=self.root_dir
        ).new_file()
        self.runtime_zypp_config_file = Temporary(
            dir=self.root_dir
        ).new_file()

        self.zypper_args = [
            '--non-interactive',
            '--gpg-auto-import-keys',
            '--pkg-cache-dir', self.shared_zypper_dir['pkg-cache-dir'],
            '--reposd-dir', self.shared_zypper_dir['reposd-dir'],
            '--solv-cache-dir', self.shared_zypper_dir['solv-cache-dir'],
            '--cache-dir', self.shared_zypper_dir['cache-dir'],
            '--raw-cache-dir', self.shared_zypper_dir['raw-cache-dir'],
            '--config', self.runtime_zypper_config_file.name
        ] + self.custom_args

        self.command_env = self._create_zypper_runtime_environment()

        # config file parameters for zypper tool
        self.runtime_zypper_config = ConfigParser()
        self.runtime_zypper_config.add_section('main')

        # config file parameters for libzypp library
        self.runtime_zypp_config = ConfigParser()
        self.runtime_zypp_config.add_section('main')
        self.runtime_zypp_config.set(
            'main', 'credentials.global.dir',
            self.shared_zypper_dir['credentials-dir']
        )
        if self.target_arch:
            self.runtime_zypp_config.set(
                'main', 'arch', self.target_arch
            )
        if self.exclude_docs:
            self.runtime_zypp_config.set(
                'main', 'rpm.install.excludedocs', 'yes'
            )

        if self.gpgcheck:
            self.runtime_zypp_config.set(
                'main', 'gpgcheck', '1'
            )
        else:
            self.runtime_zypp_config.set(
                'main', 'gpgcheck', '0'
            )

        self._write_runtime_config()

    def setup_package_database_configuration(self) -> None:
        """
        Setup rpm macros for bootstrapping and image building

        1. Create the rpm image macro which persists during the build
        2. Create the rpm bootstrap macro to make sure for bootstrapping
           the rpm database location matches the host rpm database setup.
           This macro only persists during the bootstrap phase. If the
           image was already bootstrapped a compat link is created instead.
        3. Create zypper compat link
        """
        rpmdb = RpmDataBase(
            self.root_dir, Defaults.get_custom_rpm_image_macro_name()
        )
        if self.locale:
            rpmdb.set_macro_from_string(self.locale)
        rpmdb.write_config()

        rpmdb = RpmDataBase(self.root_dir)
        if rpmdb.has_rpm():
            rpmdb.link_database_to_host_path()
        else:
            rpmdb.set_database_to_host_path()
        # Zypper compat code:
        #
        # Manually adding the compat link /var/lib/rpm that points to the
        # rpmdb location as it is configured in the host rpm setup. The
        # host rpm setup is taken into account because import_trusted_keys
        # is called during the bootstrap phase where rpm (respectively zypper)
        # is called from the host
        #
        # Usually it is expected that the package manager reads the
        # signing keys from the rpm database setup provisioned by rpm
        # itself (macro level) but zypper doesn't take the rpm macro
        # setup into account and relies on a hard coded path which we
        # can only provide as a symlink.
        #
        # That symlink is usually created by the rpm package when it gets
        # installed. However at that early phase when we import the
        # signing keys no rpm is installed yet nor any symlink exists.
        # Thus we have to create it here and hope to get rid of it in the
        # future.
        #
        # For further details on the motivation in zypper please
        # refer to bsc#1112357
        rpmdb.init_database()
        image_rpm_compat_link = '/var/lib/rpm'
        host_rpm_dbpath = rpmdb.rpmdb_host.expand_query('%_dbpath')
        if host_rpm_dbpath != image_rpm_compat_link:
            Path.create(
                self.root_dir + os.path.dirname(image_rpm_compat_link)
            )
            Command.run(
                [
                    'ln', '-s', '--no-target-directory',
                    ''.join(['../..', host_rpm_dbpath]),
                    self.root_dir + image_rpm_compat_link
                ], raise_on_error=False
            )

    def use_default_location(self) -> None:
        """
        Setup zypper repository operations to store all data
        in the default places
        """
        self.shared_zypper_dir['reposd-dir'] = \
            self.root_dir + '/etc/zypp/repos.d'
        self.shared_zypper_dir['credentials-dir'] = \
            self.root_dir + '/etc/zypp/credentials.d'
        self.zypper_args = [
            '--non-interactive',
        ] + self.custom_args
        self.command_env = dict(os.environ, LANG='C')

    def runtime_config(self) -> Dict:
        """
        zypper runtime configuration and environment
        """
        return {
            'zypper_args': self.zypper_args,
            'command_env': self.command_env
        }

    def add_repo(
        self, name: str, uri: str, repo_type: str = 'rpm-md',
        prio: int = None, dist: str = None, components: str = None,
        user: str = None, secret: str = None, credentials_file: str = None,
        repo_gpgcheck: bool = False, pkg_gpgcheck: bool = False,
        sourcetype: str = None, use_for_bootstrap: bool = False,
        customization_script: str = None
    ) -> None:
        """
        Add zypper repository

        :param str name: repository name
        :param str uri: repository URI
        :param str repo_type: repostory type name
        :param int prio: zypper repostory priority
        :param str dist: unused
        :param str components: unused
        :param str user: credentials username
        :param str secret: credentials password
        :param str credentials_file: zypper credentials file
        :param bool repo_gpgcheck: enable repository signature validation
        :param bool pkg_gpgcheck: enable package signature validation
        :param str sourcetype: unused
        :param boot use_for_bootstrap: unused
        :param str customization_script:
            custom script called after the repo file was created
        """
        if credentials_file:
            repo_secret = os.sep.join(
                [self.shared_zypper_dir['credentials-dir'], credentials_file]
            )
            if os.path.exists(repo_secret):
                Path.wipe(repo_secret)

            if user and secret:
                uri = ''.join([uri, '?credentials=', credentials_file])
                with open(repo_secret, 'w') as credentials:
                    credentials.write('username={0}{1}'.format(
                        user, os.linesep)
                    )
                    credentials.write('password={0}{1}'.format(
                        secret, os.linesep)
                    )

        repo_file = ''.join(
            [self.shared_zypper_dir['reposd-dir'], '/', name, '.repo']
        )
        self.repo_names.append(''.join([name, '.repo']))

        if os.path.exists(repo_file):
            Path.wipe(repo_file)

        self._backup_package_cache()
        zypper_addrepo_command = ['zypper'] + self.zypper_args + [
            '--root', self.root_dir,
            'addrepo',
            '--refresh',
            '--keep-packages' if Uri(uri).is_remote() else
            '--no-keep-packages',
            '--no-check',
            uri,
            name
        ]
        try:
            Command.run(
                zypper_addrepo_command, self.command_env
            )
        except Exception:
            # for whatever reason zypper sometimes failes with
            # a 'failed to cache rpm database' error. I could not
            # find any reason why and a simple recall of the exact
            # same command in the exact same environment works.
            # Thus the stupid but simple workaround to this problem
            # is try one recall before really failing
            Command.run(
                zypper_addrepo_command, self.command_env
            )

        repo_config = ConfigParser()
        repo_config.read(repo_file)
        repo_config.set(
            name, 'repo_gpgcheck', '1' if repo_gpgcheck else '0'
        )
        repo_config.set(
            name, 'pkg_gpgcheck', '1' if pkg_gpgcheck else '0'
        )
        if prio:
            repo_config.set(
                name, 'priority', format(prio)
            )
        with open(repo_file, 'w') as repo:
            repo_config.write(repo)
        if customization_script:
            self.run_repo_customize(customization_script, repo_file)
        self._restore_package_cache()

    def import_trusted_keys(self, signing_keys: List) -> None:
        """
        Imports trusted keys into the image

        :param list signing_keys: list of the key files to import
        """
        rpmdb = RpmDataBase(self.root_dir)
        for key in signing_keys:
            rpmdb.import_signing_key_to_image(key)

    def delete_repo(self, name: str) -> None:
        """
        Delete zypper repository

        :param str name: repository name
        """
        Command.run(
            ['zypper'] + self.zypper_args + [
                '--root', self.root_dir, 'removerepo', name
            ],
            self.command_env
        )

    def delete_all_repos(self) -> None:
        """
        Delete all zypper repositories
        """
        Path.wipe(self.shared_zypper_dir['reposd-dir'])
        Path.create(self.shared_zypper_dir['reposd-dir'])

    def delete_repo_cache(self, name: str) -> None:
        """
        Delete zypper repository cache

        The cache data for each repository is stored in a list of
        directories of the same name as the repository name. The method
        deletes these directories to cleanup the cache information

        :param str name: repository name
        """
        Path.wipe(
            os.sep.join([self.shared_zypper_dir['pkg-cache-dir'], name])
        )
        Path.wipe(
            os.sep.join([self.shared_zypper_dir['solv-cache-dir'], name])
        )
        Path.wipe(
            os.sep.join([self.shared_zypper_dir['raw-cache-dir'], name])
        )

    def cleanup_unused_repos(self) -> None:
        """
        Delete unused zypper repositories

        zypper creates a system solvable which is unwanted for the
        purpose of building images. In addition zypper fails with
        an error message 'Failed to cache rpm database' if such a
        system solvable exists and a new root system is created

        All other repository configurations which are not used for
        this build must be removed too, otherwise they are taken into
        account for the package installations
        """
        solv_dir = self.shared_zypper_dir['solv-cache-dir']
        Path.wipe(solv_dir + '/@System')

        repos_dir = self.shared_zypper_dir['reposd-dir']
        repo_files = list(os.walk(repos_dir))[0][2]
        for repo_file in repo_files:
            if repo_file not in self.repo_names:
                Path.wipe(repos_dir + '/' + repo_file)

    def _create_zypper_runtime_environment(self) -> Dict:
        for zypper_dir in list(self.shared_zypper_dir.values()):
            Path.create(zypper_dir)
        return dict(
            os.environ,
            LANG='C',
            ZYPP_CONF=self.runtime_zypp_config_file.name
        )

    def _write_runtime_config(self) -> None:
        with open(self.runtime_zypper_config_file.name, 'w') as config:
            self.runtime_zypper_config.write(config)
        with open(self.runtime_zypp_config_file.name, 'w') as config:
            self.runtime_zypp_config.write(config)

    def _backup_package_cache(self) -> None:
        """
        preserve package cache which otherwise will be removed by
        zypper if no repo file is found. But this situation is
        normal for an image build process which setup and remove
        repos for building at runtime
        """
        self._move_package_cache(backup=True)

    def _restore_package_cache(self) -> None:
        """
        restore preserved package cache at the location passed to zypper
        """
        self._move_package_cache(restore=True)

    def _move_package_cache(self, backup: bool = False, restore: bool = False) -> None:
        package_cache = self.shared_location + '/packages'
        package_cache_moved = package_cache + '.moved'
        if backup and os.path.exists(package_cache):
            Command.run(
                ['mv', '-f', package_cache, package_cache_moved]
            )
        elif restore and os.path.exists(package_cache_moved):
            Command.run(
                ['mv', '-f', package_cache_moved, package_cache]
            )

    def __del__(self) -> None:
        self._restore_package_cache()
