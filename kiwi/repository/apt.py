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
import shutil
import hashlib
import logging
from base64 import b64encode
from urllib.parse import (
    urlparse, unquote
)
from urllib.request import (
    Request, urlopen
)
from typing import List, Dict

# project
import kiwi.defaults as defaults
from kiwi.utils.temporary import (
    Temporary, TmpT
)
from kiwi.repository.template.apt import PackageManagerTemplateAptGet
from kiwi.repository.base import RepositoryBase
from kiwi.path import Path
from kiwi.utils.toenv import ToEnv
from kiwi.system.uri import Uri

from kiwi.exceptions import KiwiUriOpenError

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
    :param str keyrings_dir: location of the repository keyring files
    :param str keyring_prefix: build specific keyring file name prefix
    :param list keyrings: keyring files referenced via Signed-By
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

        # delete custom arguments not used for apt
        for argument in self.custom_args:
            if '_install_langs' in argument or '_target_arch' in argument:
                log.warning(
                    f'Custom argument {argument} will be ignored for apt'
                )
                self.custom_args.remove(argument)

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
            'netrcparts-dir': self.manager_base + '/auth.conf.d',
            'preferences-dir': self.manager_base + '/preferences.d'
        }
        # Each signing key is stored as keyring file in keyrings_dir
        # and referenced via Signed-By from the repository sources
        # files. apt is called on the host for the bootstrap phase and
        # chrooted for the image build phase. Thus the keyring files
        # must exist at the same location on the host and in the image
        # root. The build specific prefix prevents concurrent builds
        # from using each others keyring files on the host
        self.keyrings_dir = '/etc/apt/keyrings'
        self.keyring_prefix = 'kiwi-{0}-'.format(
            hashlib.sha256(
                os.path.realpath(self.root_dir).encode()
            ).hexdigest()[:8]
        )
        self.keyrings: List[str] = []

        # former kiwi versions created a global keyring in the
        # shared location, which would still be trusted by apt
        legacy_keyring = '{}/trusted.gpg'.format(self.manager_base)
        if os.path.exists(legacy_keyring):
            os.unlink(legacy_keyring)

        self.runtime_apt_get_config_file = Temporary(
            path=self.root_dir, prefix='kiwi_apt.config'
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
        self.shared_apt_get_dir['netrcparts-dir'] = \
            os.sep.join([self.manager_base, 'auth.conf.d'])
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
        :param str user: username
        :param str secret: password_or_token
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
        auth_file = '/'.join(
            [self.shared_apt_get_dir['netrcparts-dir'], name + '.conf']
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
            if self.keyrings:
                repo_details += 'Signed-By: {0}{1}'.format(
                    ' '.join(self.keyrings), os.linesep
                )
            if repo_gpgcheck is False:
                repo_details += 'trusted: yes' + os.linesep
                repo_details += 'check-valid-until: no' + os.linesep
            repo.write(repo_details)
        if secret:
            with open(auth_file, 'w') as auth:
                if user:
                    auth.write(
                        'machine {} login {} password {}{}'.format(
                            uri, user, secret, os.linesep
                        )
                    )
                else:
                    auth.write(
                        'machine {} login {}{}'.format(
                            uri, secret, os.linesep
                        )
                    )
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
        Stores each provided key as keyring file in /etc/apt/keyrings
        on the host and in the image root. The keyring files are
        referenced via Signed-By from the repository sources files
        added afterwards

        :param list signing_keys:
            list of the key files to import. A key can be a local
            file path or a remote http, https or ftp location. Remote
            keys are downloaded prior to the import

        :raises KiwiUriOpenError: if the download of a remote key fails
        """
        self.delete_trusted_keys()
        with Temporary(prefix='kiwi_apt_keys.').new_dir() as key_dir:
            for index, key in enumerate(signing_keys):
                if urlparse(key).scheme in ('http', 'https', 'ftp'):
                    key = self._download_key(
                        key, os.sep.join([key_dir, f'key.{index}'])
                    )
                # apt expects ASCII armored keys to use the .asc
                # extension, any other key file is used as binary keyring
                with open(key, 'rb') as key_file:
                    is_armored = \
                        b'-----BEGIN PGP PUBLIC KEY BLOCK-----' in key_file.read()
                keyring_name = '{0}{1}.{2}'.format(
                    self.keyring_prefix, index, 'asc' if is_armored else 'gpg'
                )
                for keyrings_dir in self._get_keyrings_dirs():
                    Path.create(keyrings_dir)
                    target = os.sep.join([keyrings_dir, keyring_name])
                    shutil.copy(key, target)
                    # apt verifies signatures as _apt user
                    os.chmod(target, 0o644)
                keyring = os.sep.join([self.keyrings_dir, keyring_name])
                self.keyrings.append(keyring)
                log.info(f'Keyring for APT created: {keyring}')

    def delete_trusted_keys(self) -> None:
        """
        Delete the keyring files created by import_trusted_keys
        on the host and in the image root
        """
        for keyrings_dir in self._get_keyrings_dirs():
            self._delete_keyrings(keyrings_dir)
        self.keyrings = []

    @staticmethod
    def _download_key(key_url: str, target: str) -> str:
        log.info(f'Downloading signing key: {Uri.print_sensitive(key_url)}')
        uri = urlparse(key_url)
        request = Request(key_url)
        if uri.username and uri.scheme != 'ftp':
            # urllib handles credentials as part of the URL for
            # ftp only, pass them as basic auth header for http(s)
            netloc = uri.netloc.rpartition('@')[2]
            request = Request(uri._replace(netloc=netloc).geturl())
            credentials = b64encode(
                ':'.join(
                    [unquote(uri.username), unquote(uri.password or '')]
                ).encode()
            ).decode()
            request.add_header('Authorization', f'Basic {credentials}')
        try:
            with urlopen(request) as location:
                with open(target, 'wb') as key_file:
                    key_file.write(location.read())
        except Exception as issue:
            raise KiwiUriOpenError(
                'Failed to download signing key {0}: {1}: {2}'.format(
                    Uri.print_sensitive(key_url), type(issue).__name__, issue
                )
            )
        return target

    def delete_repo(self, name: str) -> None:
        """
        Delete apt-get repository

        :param str name: repository base file name
        """
        Path.wipe(
            self.shared_apt_get_dir['sources-dir'] + '/' + name + '.sources'
        )
        Path.wipe(
            self.shared_apt_get_dir['netrcparts-dir'] + '/' + name + '.conf'
        )
        Path.wipe(
            self.shared_apt_get_dir['preferences-dir'] + '/' + name + '.pref'
        )

    def delete_all_repos(self) -> None:
        """
        Delete all apt-get repositories
        """
        for dirname in ['sources-dir', 'netrcparts-dir', 'preferences-dir']:
            Path.wipe(self.shared_apt_get_dir[dirname])
            Path.create(self.shared_apt_get_dir[dirname])

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
        ToEnv(self.root_dir, defaults.PACKAGE_MANAGER_ENV_VARS)
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

    def _get_keyrings_dirs(self) -> List[str]:
        return [
            self.keyrings_dir,
            os.path.normpath(os.sep.join([self.root_dir, self.keyrings_dir]))
        ]

    def _delete_keyrings(self, keyrings_dir: str) -> None:
        for keyring in glob.glob(
            os.sep.join([keyrings_dir, f'{self.keyring_prefix}*'])
        ):
            os.unlink(keyring)

    def cleanup(self) -> None:
        """
        Delete intermediate apt config file and the keyring files
        on the host. The keyring files in the image root are still
        referenced by the repository sources files and are deleted
        via delete_trusted_keys at the end of the build
        """
        if os.path.isfile(self.runtime_apt_get_config_file.name):
            os.unlink(self.runtime_apt_get_config_file.name)
        self._delete_keyrings(self.keyrings_dir)
