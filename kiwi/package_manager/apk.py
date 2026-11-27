# Copyright (c) 2025 SUSE LLC.  All rights reserved.
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
from typing import List, Dict, Optional

# project
from kiwi.utils.install_progress import PackageManagerEventT
from kiwi.command import CommandCallT
from kiwi.command import Command
from kiwi.package_manager.base import PackageManagerBase
from kiwi.system.root_bind import RootBind
from kiwi.exceptions import KiwiBootStrapPhaseFailed

log = logging.getLogger('kiwi')


# apk output lines read for the progress information
APK_PACKAGE = re.compile(
    r'^\(\s*(\d+)/(\d+)\)\s+'
    r'(Installing|Upgrading|Downgrading|Reinstalling|Replacing|Purging)'
    r'\s+(\S+)'
)
APK_SCRIPT = re.compile(r'^Executing (\S+)')


class PackageManagerApk(PackageManagerBase):
    """
    **Implements Installation/Deletion of packages/collections with apk**

    :param dict command_env:
        apk command environment from repository
        runtime configuration
    """

    def post_init(self, custom_args: Optional[List[str]] = None) -> None:
        """
        Post initialization method

        Store custom apk arguments

        :param list custom_args: custom apk arguments
        """
        self.custom_args: List[str] = custom_args or []

        runtime_config = self.repository.runtime_config()
        self.command_env = runtime_config['command_env']
        self.bootstrap_repo = runtime_config['bootstrap_repo']

    def request_package(self, name: str) -> None:
        """
        Queue a package request

        :param str name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name: str) -> None:
        """
        Queue a collection request

        apk does not distinguish the installation of packages
        and collections. Because of that collections are listed together
        with package requests and a warning message is shown.

        :param str name: apk group name
        """
        log.warning(
            (
                'apk treats collection installations as regular packages.'
                'It is preferred to list them as regular packages'
            )
        )
        self.package_requests.append(name)

    def request_product(self, name: str) -> None:
        """
        Queue a product request

        There is no product definition in the Alpine Linux repo data

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
        Repository modules not supported for apk.
        The method does nothing in this scope

        :param dict collection_modules: unused
        """
        pass

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
        if not self.bootstrap_repo:
            raise KiwiBootStrapPhaseFailed(
                'No bootstrap repository URI available'
            )
        if not self.package_requests:
            self.package_requests.append('alpine-base')
        apk_command = (
            ['apk']
            + ['--root', self.root_dir]
            + self.custom_args
            + [
                '-X',
                self.bootstrap_repo,
                '-U',
                '--allow-untrusted',
                '--initdb',
                'add',
            ]
            + self.package_requests
        )
        self.cleanup_requests()
        return Command.call(apk_command, self.command_env)

    def process_install_requests(self) -> CommandCallT:
        """
        Process package install requests for image phase (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        Command.run(
            ['chroot', self.root_dir, 'apk', 'update'], self.command_env
        )
        apk_command = (
            ['chroot', self.root_dir, 'apk']
            + self.custom_args
            + ['add']
            + self.package_requests
        )
        self.cleanup_requests()
        return Command.call(apk_command, self.command_env)

    def process_delete_requests(self, force: bool = False) -> CommandCallT:
        """
        Process package delete requests (chroot)

        :param bool force: force deletion: unused

        :raises KiwiRequestError: if none of the packages to delete is
            installed
        :return: process results in command type

        :rtype: namedtuple
        """
        Command.run(
            ['chroot', self.root_dir, 'apk', 'update'], self.command_env
        )
        apk_command = (
            ['chroot', self.root_dir, 'apk']
            + self.custom_args
            + ['del']
            + self.package_requests
        )
        self.cleanup_requests()
        return Command.call(apk_command, self.command_env)

    def update(self) -> CommandCallT:
        """
        Process package update requests (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        Command.run(
            ['chroot', self.root_dir, 'apk', 'update'], self.command_env
        )
        return Command.call(
            ['chroot', self.root_dir, 'apk', 'upgrade'] + self.custom_args,
            self.command_env,
        )

    def process_only_required(self) -> None:
        """
        Setup package processing only for required packages.

        This is the only option in apk, nothing to do here.
        """
        pass

    def process_plus_recommended(self) -> None:
        """
        Setup package processing to also include recommended dependencies.

        There is no such concept of recommended dependencies in apk.
        """
        pass

    progress_phases = ['install']

    def get_progress_event(
        self, package_manager_output: str
    ) -> Optional[PackageManagerEventT]:
        """
        Progress event from a line of apk output

        apk reports the position of each package it installs, e.g
        (12/48) Installing bash (5.2-r0), and the package scripts
        it runs, e.g Executing bash-5.2-r0.post-install

        :param str package_manager_output: line of output

        :return: progress event or None

        :rtype: PackageManagerEventT
        """
        line = package_manager_output.strip()
        match = APK_PACKAGE.match(line)
        if match:
            return PackageManagerEventT(
                phase='install',
                description=f'{match.group(3)} {match.group(4)}',
                current=int(match.group(1)),
                total=int(match.group(2)),
                package=match.group(4),
                removed=match.group(3) == 'Purging',
            )
        match = APK_SCRIPT.match(line)
        if match:
            return PackageManagerEventT(
                phase='script',
                description=f'Executing {match.group(1)}',
                package=match.group(1),
            )
        return None
