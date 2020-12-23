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
import glob
from configparser import ConfigParser
from tempfile import NamedTemporaryFile

# project
from kiwi.defaults import Defaults
from kiwi.command import Command
from kiwi.repository.base import RepositoryBase
from kiwi.path import Path
from kiwi.utils.rpm_database import RpmDataBase


class RepositoryDnf(RepositoryBase):
    """
    **Implements repository handling for dnf package manager**

    :param str shared_dnf_dir: shared directory between image root
        and build system root
    :param str runtime_dnf_config_file: dnf runtime config file name
    :param dict command_env: customized os.environ for dnf
    :param str runtime_dnf_config: instance of :class:`ConfigParser`
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom dnf arguments and create runtime configuration
        and environment

        :param list custom_args: dnf arguments
        """
        self.custom_args = custom_args
        self.exclude_docs = False
        if not custom_args:
            self.custom_args = []

        # extract custom arguments not used in dnf call
        if 'exclude_docs' in self.custom_args:
            self.custom_args.remove('exclude_docs')
            self.exclude_docs = True

        if 'check_signatures' in self.custom_args:
            self.custom_args.remove('check_signatures')
            self.gpg_check = '1'
        else:
            self.gpg_check = '0'

        self.locale = list(
            item for item in self.custom_args if '_install_langs' in item
        )
        if self.locale:
            self.custom_args.remove(self.locale[0])

        self.repo_names = []

        # dnf support is based on creating repo files which contains
        # path names to the repo and its cache. In order to allow a
        # persistent use of the files in and outside of a chroot call
        # an active bind mount from RootBind::mount_shared_directory
        # is expected and required
        manager_base = self.shared_location + '/dnf'

        self.shared_dnf_dir = {
            'reposd-dir': manager_base + '/repos',
            'cache-dir': manager_base + '/cache',
            'pluginconf-dir': manager_base + '/pluginconf',
            'vars-dir': manager_base + '/vars'
        }

        self.runtime_dnf_config_file = NamedTemporaryFile(
            dir=self.root_dir
        )

        self.dnf_args = [
            '--config', self.runtime_dnf_config_file.name, '-y'
        ] + self.custom_args

        self.command_env = self._create_dnf_runtime_environment()

        # config file parameters for dnf tool
        self._create_runtime_config_parser()
        self._create_runtime_plugin_config_parser()
        self._write_runtime_config()

    def setup_package_database_configuration(self):
        """
        Setup rpm macros for bootstrapping and image building

        1. Create the rpm image macro which persists during the build
        2. Create the rpm bootstrap macro to make sure for bootstrapping
           the rpm database location matches the host rpm database setup.
           This macro only persists during the bootstrap phase. If the
           image was already bootstrapped a compat link is created instead.
        """
        rpmdb = RpmDataBase(
            self.root_dir, Defaults.get_custom_rpm_image_macro_name()
        )
        if self.locale:
            rpmdb.set_macro_from_string(self.locale[0])
        rpmdb.write_config()

        rpmdb = RpmDataBase(self.root_dir)
        if rpmdb.has_rpm():
            rpmdb.link_database_to_host_path()
        else:
            rpmdb.set_database_to_host_path()
        # SUSE compat code:
        #
        # Manually adding the compat link /var/lib/rpm that points to the
        # rpmdb location as it is configured in the host rpm setup. DNF makes
        # use of the host setup to bootstrap or to read the signing keys
        # from the rpm database setup provisioned by rpm itself (macro level).
        # It assumes the host setup is the default for the system being built.
        #
        # For SUSE this is causing a mismatch as the host setup is not the RPM
        # default (/var/lib/rpm) and SUSE distros proactively relocate the rpm
        # database from the default location to a custom one when the
        # rpm package and related macros are installed for the first time.
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

    def use_default_location(self):
        """
        Setup dnf repository operations to store all data
        in the default places
        """
        self.shared_dnf_dir['reposd-dir'] = \
            self.root_dir + '/etc/yum.repos.d'
        self.shared_dnf_dir['cache-dir'] = \
            self.root_dir + '/var/cache/dnf'
        self.shared_dnf_dir['pluginconf-dir'] = \
            self.root_dir + '/etc/dnf/plugins'
        self.shared_dnf_dir['vars-dir'] = \
            self.root_dir + '/etc/dnf/vars'
        self._create_runtime_config_parser()
        self._create_runtime_plugin_config_parser()
        self._write_runtime_config()

    def runtime_config(self):
        """
        dnf runtime configuration and environment

        :return: dnf_args:list, command_env:dict

        :rtype: dict
        """
        return {
            'dnf_args': self.dnf_args,
            'command_env': self.command_env
        }

    def add_repo(
        self, name, uri, repo_type='rpm-md',
        prio=None, dist=None, components=None,
        user=None, secret=None, credentials_file=None,
        repo_gpgcheck=None, pkg_gpgcheck=None,
        sourcetype=None, use_for_bootstrap=False
    ):
        """
        Add dnf repository

        :param str name: repository base file name
        :param str uri: repository URI
        :param repo_type: repostory type name
        :param int prio: dnf repostory priority
        :param str dist: unused
        :param str components: unused
        :param str user: unused
        :param str secret: unused
        :param str credentials_file: unused
        :param bool repo_gpgcheck: enable repository signature validation
        :param bool pkg_gpgcheck: enable package signature validation
        :param str sourcetype:
            source type, one of 'baseurl', 'metalink' or 'mirrorlist'
        :param bool use_for_bootstrap: unused
        """
        repo_file = self.shared_dnf_dir['reposd-dir'] + '/' + name + '.repo'
        self.repo_names.append(name + '.repo')
        if os.path.exists(uri):
            # dnf requires local paths to take the file: type
            uri = 'file://' + uri
        repo_config = ConfigParser()
        repo_config.add_section(name)
        repo_config.set(
            name, 'name', name
        )
        repo_config.set(
            name, sourcetype if sourcetype else 'baseurl', uri
        )
        if prio:
            repo_config.set(
                name, 'priority', format(prio)
            )
        if repo_gpgcheck is not None:
            repo_config.set(
                name, 'repo_gpgcheck', '1' if repo_gpgcheck else '0'
            )
        if pkg_gpgcheck is not None:
            repo_config.set(
                name, 'gpgcheck', '1' if pkg_gpgcheck else '0'
            )
        if Defaults.is_buildservice_worker():
            # when building in the build service, modular metadata is inaccessible...
            # in order to use modular content in the build service, we need to disable
            # modular filtering, which is done with module_hotfixes option
            repo_config.set(
                name, 'module_hotfixes', '1'
            )
        with open(repo_file, 'w') as repo:
            repo_config.write(repo)

    def import_trusted_keys(self, signing_keys):
        """
        Imports trusted keys into the image

        :param list signing_keys: list of the key files to import
        """
        rpmdb = RpmDataBase(self.root_dir)
        for key in signing_keys:
            rpmdb.import_signing_key_to_image(key)

    def delete_repo(self, name):
        """
        Delete dnf repository

        :param str name: repository base file name
        """
        Path.wipe(
            self.shared_dnf_dir['reposd-dir'] + '/' + name + '.repo'
        )

    def delete_all_repos(self):
        """
        Delete all dnf repositories
        """
        Path.wipe(self.shared_dnf_dir['reposd-dir'])
        Path.create(self.shared_dnf_dir['reposd-dir'])

    def delete_repo_cache(self, name):
        """
        Delete dnf repository cache

        The cache data for each repository is stored in a directory
        and additional files all starting with the repository name.
        The method glob deletes all files and directories matching
        the repository name followed by any characters to cleanup
        the cache information

        :param str name: repository name
        """
        dnf_cache_glob_pattern = ''.join(
            [self.shared_dnf_dir['cache-dir'], os.sep, name, '*']
        )
        for dnf_cache_file in glob.iglob(dnf_cache_glob_pattern):
            Path.wipe(dnf_cache_file)

    def cleanup_unused_repos(self):
        """
        Delete unused dnf repositories

        Repository configurations which are not used for this build
        must be removed otherwise they are taken into account for
        the package installations
        """
        repos_dir = self.shared_dnf_dir['reposd-dir']
        repo_files = list(os.walk(repos_dir))[0][2]
        for repo_file in repo_files:
            if repo_file not in self.repo_names:
                Path.wipe(repos_dir + '/' + repo_file)

    def _create_dnf_runtime_environment(self):
        for dnf_dir in list(self.shared_dnf_dir.values()):
            Path.create(dnf_dir)
        return dict(
            os.environ, LANG='C'
        )

    def _create_runtime_config_parser(self):
        self.runtime_dnf_config = ConfigParser()
        self.runtime_dnf_config.add_section('main')

        self.runtime_dnf_config.set(
            'main', 'cachedir', self.shared_dnf_dir['cache-dir']
        )
        self.runtime_dnf_config.set(
            'main', 'reposdir', self.shared_dnf_dir['reposd-dir']
        )
        self.runtime_dnf_config.set(
            'main', 'varsdir', self.shared_dnf_dir['vars-dir']
        )
        self.runtime_dnf_config.set(
            'main', 'pluginconfpath', self.shared_dnf_dir['pluginconf-dir']
        )
        self.runtime_dnf_config.set(
            'main', 'keepcache', '1'
        )
        self.runtime_dnf_config.set(
            'main', 'debuglevel', '2'
        )
        self.runtime_dnf_config.set(
            'main', 'best', '1'
        )
        self.runtime_dnf_config.set(
            'main', 'obsoletes', '1'
        )
        self.runtime_dnf_config.set(
            'main', 'plugins', '1'
        )
        self.runtime_dnf_config.set(
            'main', 'gpgcheck', self.gpg_check
        )
        if self.exclude_docs:
            self.runtime_dnf_config.set(
                'main', 'tsflags', 'nodocs'
            )

    def _create_runtime_plugin_config_parser(self):
        self.runtime_dnf_plugin_config = ConfigParser()
        self.runtime_dnf_plugin_config.add_section('main')

        self.runtime_dnf_plugin_config.set(
            'main', 'enabled', '1'
        )

    def _write_runtime_config(self):
        with open(self.runtime_dnf_config_file.name, 'w') as config:
            self.runtime_dnf_config.write(config)
        if os.path.exists(self.shared_dnf_dir['pluginconf-dir']):
            dnf_plugin_config_file = \
                self.shared_dnf_dir['pluginconf-dir'] + '/priorities.conf'
            with open(dnf_plugin_config_file, 'w') as pluginconfig:
                self.runtime_dnf_plugin_config.write(pluginconfig)
