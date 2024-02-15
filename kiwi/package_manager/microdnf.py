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
import re
import logging
from typing import (
    List, Dict
)


# project
from kiwi.command import CommandCallT
from kiwi.command import Command
from kiwi.utils.rpm_database import RpmDataBase
from kiwi.utils.rpm import Rpm
from kiwi.package_manager.base import PackageManagerBase
from kiwi.system.root_bind import RootBind
from kiwi.path import Path
from kiwi.defaults import Defaults
from kiwi.repository.dnf4 import RepositoryDnf4

from kiwi.exceptions import KiwiRequestError

log = logging.getLogger('kiwi')


class PackageManagerMicroDnf(PackageManagerBase):
    """
    **Implements Installation/Deletion of packages/collections with microdnf***

    :param doct dnf_args:
        microdnf arguments from repository runtime configuration
    :param dict command_env:
        microdnf command environment from repository runtime
        configuration
    """
    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        :param list custom_args: custom microdnf arguments
        """
        self.repository: RepositoryDnf4 = self.repository
        self.custom_args = custom_args

        runtime_config = self.repository.runtime_config()
        self.dnf_args = runtime_config['dnf_args']
        self.command_env = runtime_config['command_env']

    def request_package(self, name: str) -> None:
        """
        Queue a package request

        :param str name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name: str) -> None:
        """
        Queue a collection request

        :param str name: dnf group name
        """
        log.warning(
            'Group(%s) handling not yet supported for microdnf', name
        )

    def request_product(self, name: str) -> None:
        """
        Queue a product request

        There is no product definition in the fedora repo data

        :param str name: unused
        """
        pass

    def request_package_exclusion(self, name: str) -> None:
        """
        Queue a package exclusion(skip) request

        :param str name: package name
        """
        self.exclude_requests.append(name)

    def setup_repository_modules(
        self, collection_modules: Dict[str, List[str]]
    ) -> None:
        """
        Setup repository modules and streams

        :param dict collection_modules:
            Expect dict of the form:

            .. code:: python

                {
                    'enable': [
                        "module:stream", "module"
                    ],
                    'disable': [
                        "module"
                    ]
                }
        """
        microdnf_module_command = [
            'microdnf'
        ] + ['--refresh'] + self.dnf_args + [
            '--installroot', self.root_dir,
            f'--releasever={self.release_version}',
            '--noplugins',
            '--setopt=cachedir={0}'.format(
                self.repository.shared_dnf_dir['cache-dir']
            ),
            '--setopt=reposdir={0}'.format(
                self.repository.shared_dnf_dir['reposd-dir']
            ),
            '--setopt=varsdir={0}'.format(
                self.repository.shared_dnf_dir['vars-dir']
            )
        ] + self.custom_args + [
            'module'
        ]
        for disable_module in collection_modules['disable']:
            Command.run(
                microdnf_module_command + [
                    'disable', disable_module
                ], self.command_env
            )
        for enable_module in collection_modules['enable']:
            Command.run(
                microdnf_module_command + [
                    'reset', enable_module.split(':')[0]
                ], self.command_env
            )
            Command.run(
                microdnf_module_command + [
                    'enable', enable_module
                ], self.command_env
            )

    def process_install_requests_bootstrap(
        self, root_bind: RootBind = None, bootstrap_package: str = None
    ) -> CommandCallT:
        """
        Process package install requests for bootstrap phase (no chroot)

        :param object root_bind: unused
        :param str bootstrap_package: unused

        :return: process results in command type

        :rtype: namedtuple
        """
        microdnf_command = [
            'microdnf'
        ] + ['--refresh'] + self.dnf_args + [
            '--installroot', self.root_dir,
            f'--releasever={self.release_version}',
            '--noplugins',
            '--setopt=cachedir={0}'.format(
                self.repository.shared_dnf_dir['cache-dir']
            ),
            '--setopt=reposdir={0}'.format(
                self.repository.shared_dnf_dir['reposd-dir']
            ),
            '--setopt=varsdir={0}'.format(
                self.repository.shared_dnf_dir['vars-dir']
            )
        ] + self.custom_args + ['install'] + self.package_requests
        self.cleanup_requests()
        return Command.call(
            microdnf_command, self.command_env
        )

    def process_install_requests(self) -> CommandCallT:
        """
        Process package install requests for image phase (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        exclude_args = []
        if self.exclude_requests:
            # For DNF, excluding a package means removing it from
            # the solver operation. This is done by adding --exclude
            # to the command line. This means that if the package is
            # hard required by another package, it will break the transaction.
            for package in self.exclude_requests:
                exclude_args.append('--exclude=' + package)
        chroot_dnf_args = Path.move_to_root(
            self.root_dir, self.dnf_args
        )
        microdnf_command = [
            'chroot', self.root_dir, 'microdnf'
        ] + chroot_dnf_args + [
            f'--releasever={self.release_version}'
        ] + self.custom_args + exclude_args + [
            'install'
        ] + self.package_requests
        self.cleanup_requests()
        return Command.call(
            microdnf_command, self.command_env
        )

    def process_delete_requests(self, force: bool = False) -> CommandCallT:
        """
        Process package delete requests (chroot)

        :param bool force: force deletion: true|false

        :raises KiwiRequestError: if none of the packages to delete is
            installed.
        :return: process results in command type

        :rtype: namedtuple
        """
        if force:
            delete_items = []
            for delete_item in self.package_requests:
                try:
                    Command.run(
                        ['chroot', self.root_dir, 'rpm', '-q', delete_item]
                    )
                    delete_items.append(delete_item)
                except Exception:
                    # ignore packages which are not installed
                    pass
            if not delete_items:
                raise KiwiRequestError(
                    'None of the requested packages to delete are installed'
                )
            self.cleanup_requests()
            delete_options = ['--nodeps', '--allmatches', '--noscripts']
            return Command.call(
                [
                    'chroot', self.root_dir, 'rpm', '-e'
                ] + delete_options + delete_items,
                self.command_env
            )
        else:
            chroot_dnf_args = Path.move_to_root(self.root_dir, self.dnf_args)
            dnf_command = [
                'chroot', self.root_dir, 'microdnf'
            ] + chroot_dnf_args + [
                f'--releasever={self.release_version}'
            ] + self.custom_args + [
                'remove'
            ] + self.package_requests
            self.cleanup_requests()
            return Command.call(
                dnf_command, self.command_env
            )

    def update(self) -> CommandCallT:
        """
        Process package update requests (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        chroot_dnf_args = Path.move_to_root(self.root_dir, self.dnf_args)
        return Command.call(
            [
                'chroot', self.root_dir, 'microdnf'
            ] + chroot_dnf_args + [
                f'--releasever={self.release_version}'
            ] + self.custom_args + [
                'upgrade'
            ],
            self.command_env
        )

    def process_only_required(self) -> None:
        """
        Setup package processing only for required packages
        """
        if '--setopt=install_weak_deps=0' not in self.custom_args:
            self.custom_args.append('--setopt=install_weak_deps=0')

    def process_plus_recommended(self) -> None:
        """
        Setup package processing to also include recommended dependencies.
        """
        if '--setopt=install_weak_deps=0' in self.custom_args:
            self.custom_args.remove('--setopt=install_weak_deps=0')

    def match_package_installed(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        """
        Match expression to indicate a package has been installed

        This match for the package to be installed in the output
        of the microdnf command is not 100% accurate. There might
        be false positives due to sub package names starting with
        the same base package name

        :param str package_name: package_name
        :param str package_manager_output: microdnf status line

        :returns: True|False

        :rtype: bool
        """
        return bool(
            re.match(
                '.*Installing  : {0}.*'.format(re.escape(package_name)),
                package_manager_output
            )
        )

    def match_package_deleted(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        """
        Match expression to indicate a package has been deleted

        :param str package_name: package_name
        :param str package_manager_output: microdnf status line

        :returns: True|False

        :rtype: bool
        """
        return bool(
            re.match(
                '.*Removing: {0}.*'.format(re.escape(package_name)),
                package_manager_output
            )
        )

    def post_process_install_requests_bootstrap(
        self, root_bind: RootBind = None, delta_root: bool = False
    ) -> None:
        """
        Move the rpm database to the place as it is expected by the
        rpm package installed during bootstrap phase

        :param object root_bind: unused
        :param bool delta_root: unused
        """
        rpmdb = RpmDataBase(self.root_dir)
        if rpmdb.has_rpm():
            rpmdb.rebuild_database()
            rpmdb.set_database_to_image_path()

    def clean_leftovers(self) -> None:
        """
        Cleans package manager related data not needed in the
        resulting image such as custom macros
        """
        Rpm(
            self.root_dir, Defaults.get_custom_rpm_image_macro_name()
        ).wipe_config()
