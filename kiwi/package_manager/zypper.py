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
import os
from typing import List, Dict, Optional

# project
from kiwi.utils.install_progress import PackageManagerEventT
from kiwi.command import CommandCallT
from kiwi.command import Command
from kiwi.package_manager.base import PackageManagerBase
from kiwi.system.root_bind import RootBind
from kiwi.utils.rpm_database import RpmDataBase
from kiwi.utils.rpm import Rpm
from kiwi.path import Path
from kiwi.exceptions import KiwiRequestError
from kiwi.defaults import Defaults


# zypper output lines read for the progress information
ZYPPER_DOWNLOAD = re.compile(
    r'^Retrieving:? (?:package )?(\S+).*\(\s*(\d+)/(\d+)\)'
)
ZYPPER_PACKAGE = re.compile(
    r'^\(\s*(\d+)/(\d+)\) (Installing|Removing):? (\S+)'
)
ZYPPER_PRELOAD = re.compile(r'^Preloading: (\S+?)(?:\.rpm)? \[')
ZYPPER_SUMMARY = re.compile(r'^\d+ (?:new )?packages? to \w+')
ZYPPER_SUMMARY_ITEM = re.compile(
    r'^(\d+) (?:packages? )?(?:to )?(new|install|upgrade|downgrade|reinstall)'
)
ZYPPER_SCRIPT = re.compile(r'^(%\w+)\((\S+)\) script output:')
ZYPPER_SCRIPTS = 'Running post-transaction scripts'


class PackageManagerZypper(PackageManagerBase):
    """
    **Implements Installation/Deletion of packages/collections with zypper**

    :param list zypper_args:
        zypper arguments from repository runtime configuration
    :param dict command_env:
        zypper command environment from repository
        runtime configuration
    """

    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Store custom zypper arguments

        :param list custom_args: custom zypper arguments
        """
        self.anonymousId_file = '/var/lib/zypp/AnonymousUniqueId'
        self.custom_args = custom_args

        runtime_config = self.repository.runtime_config()

        self.zypper_args = runtime_config['zypper_args']
        self.chroot_zypper_args = Path.move_to_root(
            self.root_dir, self.zypper_args
        )

        self.command_env = runtime_config['command_env']
        self.chroot_command_env = dict(self.command_env)
        if 'ZYPP_CONF' in self.command_env:
            self.chroot_command_env['ZYPP_CONF'] = Path.move_to_root(
                self.root_dir, [self.command_env['ZYPP_CONF']]
            )[0]

    def request_package(self, name: str) -> None:
        """
        Queue a package request

        :param str name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name: str) -> None:
        """
        Queue a collection request

        :param str name: zypper pattern name
        """
        self.collection_requests.append('pattern:' + name)

    def request_product(self, name: str) -> None:
        """
        Queue a product request

        :param str name: zypper product name
        """
        self.product_requests.append('product:' + name)

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
        Repository modules not supported for zypper.
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
        command = (
            ['zypper']
            + self.zypper_args
            + [
                '--root',
                self.root_dir,
                'install',
                '--download',
                'in-advance',
                '--auto-agree-with-licenses',
            ]
            + self.custom_args
            + ['--']
            + self._install_items()
        )
        return Command.call(command, self.command_env)

    def process_install_requests(self) -> CommandCallT:
        """
        Process package install requests for image phase (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        if self.exclude_requests:
            # For zypper excluding a package means, removing it from
            # the solver operation. This is done by adding a package
            # lock. This means that if the package is hard required
            # by another package, it will break the transaction.
            metadata_dir = ''.join([self.root_dir, '/etc/zypp'])
            if not os.path.exists(metadata_dir):
                Path.create(metadata_dir)
            for package in self.exclude_requests:
                Command.run(
                    ['chroot', self.root_dir, 'zypper']
                    + self.chroot_zypper_args
                    + ['al']
                    + [package],
                    self.chroot_command_env,
                )
        return Command.call(
            ['chroot', self.root_dir, 'zypper']
            + self.chroot_zypper_args
            + [
                'install',
                '--download',
                'in-advance',
                '--auto-agree-with-licenses',
            ]
            + self.custom_args
            + ['--']
            + self._install_items(),
            self.chroot_command_env,
        )

    def process_delete_requests(self, force: bool = False) -> CommandCallT:
        """
        Process package delete requests (chroot)

        :param bool force: force deletion: true|false

        :raises KiwiRequestError: if none of the packages to delete is
            installed
        :return: process results in command type

        :rtype: namedtuple
        """
        if force:
            delete_items = []
            for delete_item in self._delete_items():
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
            force_options = ['--nodeps', '--allmatches', '--noscripts']
            return Command.call(
                ['chroot', self.root_dir, 'rpm', '-e']
                + force_options
                + delete_items,
                self.chroot_command_env,
            )
        else:
            zypper_command = (
                ['chroot', self.root_dir, 'zypper']
                + self.chroot_zypper_args
                + ['remove', '-u', '--force-resolution']
                + self._delete_items()
            )
            self.cleanup_requests()
            return Command.call(zypper_command, self.chroot_command_env)

    def update(self) -> CommandCallT:
        """
        Process package update requests (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        return Command.call(
            ['chroot', self.root_dir, 'zypper']
            + self.chroot_zypper_args
            + [
                'update',
                '--download',
                'in-advance',
                '--auto-agree-with-licenses',
            ]
            + self.custom_args,
            self.chroot_command_env,
        )

    def process_only_required(self) -> None:
        """
        Setup package processing only for required packages
        """
        if '--no-recommends' not in self.custom_args:
            self.custom_args.append('--no-recommends')

    def process_plus_recommended(self) -> None:
        """
        Setup package processing to also include recommended dependencies.
        """
        if '--no-recommends' in self.custom_args:
            self.custom_args.remove('--no-recommends')

    progress_phases = ['download', 'install']

    def get_progress_event(
        self, package_manager_output: str
    ) -> Optional[PackageManagerEventT]:
        """
        Progress event from a line of zypper output

        zypper reports the position of each package in the download
        and in the installation, e.g (12/148) Installing: bash.
        Packages downloaded in advance, e.g Preloading: bash.rpm [done],
        are counted as download against the number of packages from
        the summary of the transaction, e.g 148 new packages to install.
        Package scripts run after the installation are reported
        if they write output, e.g %posttrans(udev) script output:

        :param str package_manager_output: line of output

        :return: progress event or None

        :rtype: PackageManagerEventT
        """
        line = package_manager_output.strip()
        match = ZYPPER_PACKAGE.match(line)
        if match:
            removed = match.group(3) == 'Removing'
            return PackageManagerEventT(
                phase='install',
                description=f'{match.group(3)} {match.group(4)}',
                current=int(match.group(1)),
                total=int(match.group(2)),
                package=match.group(4),
                removed=removed,
            )
        match = ZYPPER_DOWNLOAD.match(line)
        if match:
            return PackageManagerEventT(
                phase='download',
                description=f'Downloading {match.group(1)}',
                current=int(match.group(2)),
                total=int(match.group(3)),
            )
        match = ZYPPER_PRELOAD.match(line)
        if match:
            return PackageManagerEventT(
                phase='download', description=f'Downloading {match.group(1)}'
            )
        if ZYPPER_SUMMARY.match(line):
            # e.g 2 packages to upgrade, 3 new, 1 to remove. Count the
            # packages zypper downloads, removed packages are not
            total = 0
            for item in line.rstrip('.').split(', '):
                match = ZYPPER_SUMMARY_ITEM.match(item)
                if match:
                    total += int(match.group(1))
            return PackageManagerEventT(phase='total', total=total)
        match = ZYPPER_SCRIPT.match(line)
        if match:
            script = f'{match.group(1)}({match.group(2)})'
            return PackageManagerEventT(
                phase='script', description=f'Running {script}', package=script
            )
        if line.startswith(ZYPPER_SCRIPTS):
            return PackageManagerEventT(
                phase='script', description=ZYPPER_SCRIPTS
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

    @staticmethod
    def has_failed(returncode: int) -> bool:
        """
        Evaluate given result return code

        In zypper any return code == 0 or >= 100 is considered success.
        Any return code different from 0 and < 100 is treated as an
        error we care for. Return codes >= 100 indicates an issue
        like 'new kernel needs reboot of the system' or similar which
        we don't care in the scope of image building

        :param int returncode: return code number

        :return: True|False

        :rtype: boolean
        """
        error_codes = [
            104,  # - ZYPPER_EXIT_INF_CAP_NOT_FOUND
            105,  # - ZYPPER_EXIT_ON_SIGNAL
            106,  # - ZYPPER_EXIT_INF_REPOS_SKIPPED
            127,  # - Command Not Found
        ]
        if returncode == 0:
            # All is good
            return False
        elif returncode in error_codes:
            # Treat matching exit code as error
            return True
        elif returncode >= 100:
            # Treat all other 100 codes as non error codes
            return False

        # Treat any other error code as error
        return True

    def clean_leftovers(self) -> None:
        """
        Cleans package manager related data not needed in the
        resulting image such as custom macros
        """
        Rpm(
            self.root_dir, Defaults.get_custom_rpm_image_macro_name()
        ).wipe_config()
        id_file = os.path.normpath(
            os.sep.join([self.root_dir, self.anonymousId_file])
        )
        if os.path.exists(id_file):
            os.unlink(id_file)

    def _install_items(self) -> List:
        items = (
            self.package_requests
            + self.collection_requests
            + self.product_requests
        )
        self.cleanup_requests()
        return items

    def _delete_items(self) -> List:
        # collections and products can't be deleted
        items = []
        items += self.package_requests
        self.cleanup_requests()
        return items
