# Copyright (c) 2023 Marcus Schäfer. All rights reserved.
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


# dnf5 output lines read for the progress information
DNF5_TRANSACTION = re.compile(
    r'^\[\s*(\d+)/(\d+)\]\s+'
    r'(Installing|Upgrading|Downgrading|Reinstalling|Removing|Replacing)'
    r'\s+(\S+)'
)
DNF5_TRANSACTION_STEP = re.compile(
    r'^\[\s*(\d+)/(\d+)\]\s+(Verify package files|Prepare transaction)'
)
DNF5_DOWNLOAD = re.compile(r'^\[\s*(\d+)/(\d+)\]\s+(\S+)\s+\d+%')
DNF5_SCRIPT = re.compile(r'^>>> Running (\S+) scriptlet: (\S+)')


class PackageManagerDnf5(PackageManagerBase):
    """
    ***Implements base class for installation/deletion of
    packages and collections using the next generation dnf5***

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
            ['dnf5']
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
        exclude_args = []
        if self.exclude_requests:
            # For DNF, excluding a package means removing it from
            # the solver operation. This is done by adding --exclude
            # to the command line. This means that if the package is
            # hard required by another package, it will break the transaction.
            for package in self.exclude_requests:
                exclude_args.append('--exclude=' + package)
        Command.run(
            ['dnf5']
            + self.dnf_args
            + [f'--releasever={self.release_version}']
            + ['makecache'],
            self.command_env,
        )
        dnf_command = (
            ['dnf5']
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
            ['chroot', self.root_dir, 'dnf5']
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
            chroot_dnf_args = Path.move_to_root(self.root_dir, self.dnf_args)
            dnf_command = (
                ['chroot', self.root_dir, 'dnf5']
                + chroot_dnf_args
                + [
                    f'--releasever={self.release_version}',
                    '--setopt=clean_requirements_on_remove=true',
                ]
                + self.custom_args
                + ['remove']
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
        chroot_dnf_args = Path.move_to_root(self.root_dir, self.dnf_args)
        return Command.call(
            ['chroot', self.root_dir, 'dnf5']
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
        self.__clean_pattern_type()
        self.custom_args.append('--setopt=install_weak_deps=False')
        self.custom_args.append('--setopt=group_package_types=mandatory')

    def process_plus_recommended(self) -> None:
        """
        Setup package processing to also include recommended dependencies.
        """
        self.__clean_pattern_type()
        self.custom_args.append('--setopt=install_weak_deps=True')
        self.custom_args.append(
            '--setopt=group_package_types=default,mandatory,conditional'
        )

    progress_phases = ['download', 'install']

    def get_progress_event(
        self, package_manager_output: str
    ) -> Optional[PackageManagerEventT]:
        """
        Progress event from a line of dnf5 output

        dnf5 reports the position of each package in the download,
        e.g [12/148] bash-0:5.3-1.x86_64 100%, and of each step of the
        transaction, e.g [14/150] Installing bash-0:5.3-1.x86_64.
        Package scripts are reported when they start, e.g
        >>> Running %post scriptlet: bash-0:5.3-1.x86_64

        :param str package_manager_output: line of output

        :return: progress event or None

        :rtype: PackageManagerEventT
        """
        line = package_manager_output.strip()
        match = DNF5_TRANSACTION.match(line)
        if match:
            name = match.group(4).rstrip('.')
            return PackageManagerEventT(
                phase='install',
                description=f'{match.group(3)} {name}',
                current=int(match.group(1)),
                total=int(match.group(2)),
                # package names are cut to the column width, the
                # position makes each package unique
                package=f'{match.group(1)}:{name}',
                removed=match.group(3) == 'Removing',
            )
        match = DNF5_TRANSACTION_STEP.match(line)
        if match:
            return PackageManagerEventT(
                phase='install',
                description=match.group(3),
                current=int(match.group(1)),
                total=int(match.group(2)),
            )
        match = DNF5_DOWNLOAD.match(line)
        if match:
            return PackageManagerEventT(
                phase='download',
                description=f'Downloading {match.group(3)}',
                current=int(match.group(1)),
                total=int(match.group(2)),
            )
        match = DNF5_SCRIPT.match(line)
        if match:
            return PackageManagerEventT(
                phase='script',
                description=f'Running {match.group(1)} scriptlet '
                f'{match.group(2)}',
                package=f'{match.group(1)}({match.group(2)})',
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

    def __clean_pattern_type(self) -> None:
        """
        Setup package processing only for required packages
        """
        if '--setopt=install_weak_deps=True' in self.custom_args:
            self.custom_args.remove('--setopt=install_weak_deps=True')
        if '--setopt=install_weak_deps=False' in self.custom_args:
            self.custom_args.remove('--setopt=install_weak_deps=False')
        if (
            '--setopt=group_package_types=default,mandatory,conditional'
            in self.custom_args
        ):
            self.custom_args.remove(
                '--setopt=group_package_types=default,mandatory,conditional'
            )
        if '--setopt=group_package_types=mandatory' in self.custom_args:
            self.custom_args.remove('--setopt=group_package_types=mandatory')
