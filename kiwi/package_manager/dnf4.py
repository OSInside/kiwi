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
import re
from typing import List, Dict, Optional

# project
from kiwi.utils.install_progress import PackageManagerEventT
from kiwi.command import CommandCallT
from kiwi.command import Command
from kiwi.utils.rpm_database import RpmDataBase
from kiwi.utils.rpm import Rpm
from kiwi.package_manager.base import PackageManagerBase
from kiwi.system.root_bind import RootBind
from kiwi.path import Path
from kiwi.defaults import Defaults

from kiwi.exceptions import KiwiRequestError


# dnf output lines read for the progress information
DNF4_DOWNLOAD = re.compile(r'^\(\s*(\d+)/(\d+)\): (\S+)')
DNF4_TRANSACTION = re.compile(
    r'^(Installing|Upgrading|Downgrading|Reinstalling|Erasing|Obsoleting)'
    r'\s*:\s*(\S+)\s+(\d+)/(\d+)$'
)
DNF4_SCRIPT = re.compile(r'^Running scriptlet\s*:\s*(\S+)\s+\d+/\d+$')
DNF4_VERIFY = re.compile(r'^Verifying\s*:\s*(\S+)\s+(\d+)/(\d+)$')


class PackageManagerDnf4(PackageManagerBase):
    """
    ***Implements base class for installation/deletion of
    packages and collections using dnf***

    :param doct dnf_args: dnf arguments from repository runtime configuration
    :param dict command_env: dnf command environment from repository runtime
        configuration
    """

    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        :param list custom_args: custom dnf arguments
        """
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

        :param str name: dnf group ID name
        """
        self.collection_requests.append(f'@{name}')

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

    def _get_dnf4_binary_name(self, root: Optional[str] = None) -> str:
        """
        Identify whether dnf is 'dnf4' or 'dnf-3'

        :param str root: lookup binary name below this root directory

        :return: name of dnf4 command

        :rtype: str
        """
        dnf4_binary = 'dnf-3'
        dnf4_search_env = (
            {'PATH': os.sep.join([root, 'usr', 'bin'])} if root else None
        )

        # Python interpreter specific path
        if Path.which(
            filename='dnf4', custom_env=dnf4_search_env, access_mode=os.X_OK
        ):
            dnf4_binary = 'dnf4'

        return dnf4_binary

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
        dnf_module_command = (
            [self._get_dnf4_binary_name()]
            + self.dnf_args
            + [
                '--installroot',
                self.root_dir,
                f'--releasever={self.release_version}',
            ]
            + self.custom_args
            + ['module']
        )
        for disable_module in collection_modules['disable']:
            Command.run(
                dnf_module_command + ['disable', disable_module],
                self.command_env,
            )
        for enable_module in collection_modules['enable']:
            Command.run(
                dnf_module_command + ['reset', enable_module.split(':')[0]],
                self.command_env,
            )
            Command.run(
                dnf_module_command + ['enable', enable_module], self.command_env
            )

    def process_install_requests_bootstrap(
        self,
        root_bind: Optional[RootBind] = None,
        bootstrap_package: Optional[str] = None,
    ) -> CommandCallT:
        """
        Process package install requests for bootstrap phase (no chroot)

        :param object root_bind: unused
        :param str bootstrap_package: unused

        :return: process results in command type

        :rtype: namedtuple
        """
        dnf4 = self._get_dnf4_binary_name()
        exclude_args = []
        if self.exclude_requests:
            # For DNF, excluding a package means removing it from
            # the solver operation. This is done by adding --exclude
            # to the command line. This means that if the package is
            # hard required by another package, it will break the transaction.
            for package in self.exclude_requests:
                exclude_args.append('--exclude=' + package)
        Command.run(
            [dnf4]
            + self.dnf_args
            + [f'--releasever={self.release_version}']
            + ['makecache'],
            self.command_env,
        )
        dnf_command = (
            [dnf4]
            + self.dnf_args
            + [
                '--installroot',
                self.root_dir,
                f'--releasever={self.release_version}',
            ]
            + self.custom_args
            + exclude_args
            + ['install']
            + self.package_requests
            + self.collection_requests
        )
        self.cleanup_requests()
        return Command.call(dnf_command, self.command_env)

    def process_install_requests(self) -> CommandCallT:
        """
        Process package install requests for image phase (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        dnf4 = self._get_dnf4_binary_name(self.root_dir)
        exclude_args = []
        if self.exclude_requests:
            # For DNF, excluding a package means removing it from
            # the solver operation. This is done by adding --exclude
            # to the command line. This means that if the package is
            # hard required by another package, it will break the transaction.
            for package in self.exclude_requests:
                exclude_args.append('--exclude=' + package)
        chroot_dnf_args = Path.move_to_root(self.root_dir, self.dnf_args)
        dnf_command = (
            ['chroot', self.root_dir, dnf4]
            + chroot_dnf_args
            + [f'--releasever={self.release_version}']
            + self.custom_args
            + exclude_args
            + ['install']
            + self.package_requests
            + self.collection_requests
        )
        self.cleanup_requests()
        return Command.call(dnf_command, self.command_env)

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
                ['chroot', self.root_dir, 'rpm', '-e']
                + delete_options
                + delete_items,
                self.command_env,
            )
        else:
            dnf4 = self._get_dnf4_binary_name(self.root_dir)
            chroot_dnf_args = Path.move_to_root(self.root_dir, self.dnf_args)
            dnf_command = (
                ['chroot', self.root_dir, dnf4]
                + chroot_dnf_args
                + [f'--releasever={self.release_version}']
                + self.custom_args
                + ['autoremove']
                + self.package_requests
            )
            self.cleanup_requests()
            return Command.call(dnf_command, self.command_env)

    def update(self) -> CommandCallT:
        """
        Process package update requests (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        dnf4 = self._get_dnf4_binary_name(self.root_dir)
        chroot_dnf_args = Path.move_to_root(self.root_dir, self.dnf_args)
        return Command.call(
            ['chroot', self.root_dir, dnf4]
            + chroot_dnf_args
            + [f'--releasever={self.release_version}']
            + self.custom_args
            + ['upgrade'],
            self.command_env,
        )

    def process_only_required(self) -> None:
        """
        Setup package processing only for required packages
        """
        if '--setopt=install_weak_deps=False' not in self.custom_args:
            self.custom_args.append('--setopt=install_weak_deps=False')

    def process_plus_recommended(self) -> None:
        """
        Setup package processing to also include recommended dependencies.
        """
        if '--setopt=install_weak_deps=False' in self.custom_args:
            self.custom_args.remove('--setopt=install_weak_deps=False')

    progress_phases = ['download', 'install', 'verify']

    def get_progress_event(
        self, package_manager_output: str
    ) -> Optional[PackageManagerEventT]:
        """
        Progress event from a line of dnf output

        dnf reports the position of each package in the download,
        e.g (12/148): bash-5.1-1.x86_64.rpm, in the transaction, e.g
        Installing : bash-5.1-1.x86_64  12/148, and in the
        verification. Package scripts are reported when they run,
        e.g Running scriptlet: bash-5.1-1.x86_64  12/148

        :param str package_manager_output: line of output

        :return: progress event or None

        :rtype: PackageManagerEventT
        """
        line = package_manager_output.strip()
        match = DNF4_TRANSACTION.match(line)
        if match:
            return PackageManagerEventT(
                phase='install',
                description=f'{match.group(1)} {match.group(2)}',
                current=int(match.group(3)),
                total=int(match.group(4)),
                package=match.group(2),
                removed=match.group(1) == 'Erasing',
            )
        match = DNF4_SCRIPT.match(line)
        if match:
            return PackageManagerEventT(
                phase='script',
                description=f'Running scriptlet {match.group(1)}',
                package=match.group(1),
            )
        match = DNF4_VERIFY.match(line)
        if match:
            return PackageManagerEventT(
                phase='verify',
                description=f'Verifying {match.group(1)}',
                current=int(match.group(2)),
                total=int(match.group(3)),
            )
        match = DNF4_DOWNLOAD.match(line)
        if match:
            return PackageManagerEventT(
                phase='download',
                description=f'Downloading {match.group(3)}',
                current=int(match.group(1)),
                total=int(match.group(2)),
            )
        return None

    def post_process_install_requests_bootstrap(
        self, root_bind: Optional[RootBind] = None, delta_root: bool = False
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
