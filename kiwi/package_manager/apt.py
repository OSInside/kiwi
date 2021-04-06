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
import logging
from typing import List

# project
from kiwi.command import command_call_type
from kiwi.command import Command
from kiwi.path import Path
from kiwi.package_manager.base import PackageManagerBase
from kiwi.system.root_bind import RootBind
from kiwi.repository.apt import RepositoryApt

from kiwi.exceptions import (
    KiwiDebootstrapError,
    KiwiRequestError
)

log = logging.getLogger('kiwi')


class PackageManagerApt(PackageManagerBase):
    """
    **Implements Installation/Deletion of packages/collections with apt-get**

    :param list apt_get_args:
        apt-get arguments from repository runtime configuration
    :param dict command_env:
        apt-get command environment from repository
        runtime configuration
    """
    def post_init(self, custom_args: List = []) -> None:
        """
        Post initialization method

        Store custom apt-get arguments

        :param list custom_args: custom apt-get arguments
        """
        self.repository: RepositoryApt = self.repository
        self.custom_args = custom_args

        self.deboostrap_minbase: bool = True

        runtime_config = self.repository.runtime_config()
        self.apt_get_args = runtime_config['apt_get_args']
        self.command_env = runtime_config['command_env']
        self.distribution = runtime_config['distribution']
        self.distribution_path = runtime_config['distribution_path']

    def request_package(self, name: str) -> None:
        """
        Queue a package request

        :param str name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name: str) -> None:
        """
        Queue a collection request

        There is no collection definition in the deb repo data

        :param str name: unused
        """
        log.warning(
            'Collection(%s) handling not supported for apt-get', name
        )

    def request_product(self, name: str) -> None:
        """
        Queue a product request

        There is no product definition in the deb repo data

        :param str name: unused
        """
        log.warning(
            'Product(%s) handling not supported for apt-get', name
        )

    def request_package_exclusion(self, name: str) -> None:
        """
        Queue a package exclusion(skip) request

        Package exclusion for apt package manager not yet implemented

        :param str name: unused
        """
        log.warning(
            'Package exclusion for (%s) not supported for apt-get', name
        )

    def process_install_requests_bootstrap(
        self, root_bind: RootBind = None
    ) -> command_call_type:
        """
        Process package install requests for bootstrap phase (no chroot)
        The debootstrap program is used to bootstrap a new system with
        a collection of predefined packages. The kiwi bootstrap section
        information is not used in this case

        :param object root_bind: instance of RootBind to manage kernel
            file systems before debootstrap call

        :raises KiwiDebootstrapError: if no main distribution repository
            is configured, if the debootstrap script is not found or if the
            debootstrap script execution fails
        :return: process results in command type
        :rtype: namedtuple
        """
        if not self.distribution:
            raise KiwiDebootstrapError(
                'No main distribution repository is configured'
            )
        bootstrap_script = '/usr/share/debootstrap/scripts/' + \
            self.distribution
        if not os.path.exists(bootstrap_script):
            raise KiwiDebootstrapError(
                'debootstrap script for %s distribution not found' %
                self.distribution
            )

        # APT package manager does not support bootstrapping. To circumvent
        # this limitation there is the debootstrap tool for APT based distros.
        # Because of that there is a little overlap between KIWI and
        # debootstrap. Debootstrap manages itself the kernel file systems for
        # chroot environment, thus we need to umount the kernel file systems
        # before calling debootstrap and remount them afterwards.
        if root_bind:
            root_bind.umount_kernel_file_systems()

        # debootsrap will create its own dev/fd devices
        debootstrap_device_node_conflicts = [
            'dev/fd',
            'dev/pts'
        ]
        for node in debootstrap_device_node_conflicts:
            Path.wipe(os.path.normpath(os.sep.join([self.root_dir, node])))

        if 'apt' in self.package_requests:
            # debootstrap takes care to install apt
            self.package_requests.remove('apt')
        try:
            cmd = ['debootstrap']
            if self.repository.unauthenticated == 'false' and \
               os.path.exists(self.repository.keyring):
                cmd.append('--keyring={}'.format(self.repository.keyring))
            else:
                cmd.append('--no-check-gpg')
            if self.deboostrap_minbase:
                cmd.append('--variant=minbase')
            if self.package_requests:
                cmd.append(
                    '--include={}'.format(','.join(self.package_requests))
                )
            if self.repository.components:
                cmd.append(
                    '--components={0}'.format(
                        ','.join(self.repository.components)
                    )
                )
            self.cleanup_requests()
            cmd.extend([
                self.distribution, self.root_dir, self.distribution_path
            ])

            return Command.call(cmd, self.command_env)
        except Exception as e:
            raise KiwiDebootstrapError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def post_process_install_requests_bootstrap(
        self, root_bind: RootBind = None
    ) -> None:
        """
        Mounts the kernel file systems to the chroot environment is
        ready after the bootstrap procedure

        :param object root_bind:
            instance of RootBind to manage kernel file systems
        """
        if root_bind:
            root_bind.mount_kernel_file_systems()

    def process_install_requests(self) -> command_call_type:
        """
        Process package install requests for image phase (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        update_command = ['chroot', self.root_dir, 'apt-get']
        update_command.extend(
            Path.move_to_root(self.root_dir, self.apt_get_args)
        )
        update_command.extend(self.custom_args)
        update_command.append('update')
        Command.run(update_command, self.command_env)

        apt_get_command = ['chroot', self.root_dir, 'apt-get']
        apt_get_command.extend(
            Path.move_to_root(self.root_dir, self.apt_get_args)
        )
        apt_get_command.extend(self.custom_args)
        apt_get_command.append('install')
        apt_get_command.extend(self._package_requests())

        return Command.call(
            apt_get_command, self.command_env
        )

    def process_delete_requests(self, force: bool = False) -> command_call_type:
        """
        Process package delete requests (chroot)

        :param bool force: force deletion: true|false

        :raises KiwiRequestError: if none of the packages to delete is
            installed
        :return: process results in command type

        :rtype: namedtuple
        """
        delete_items = []
        for delete_item in self._package_requests():
            try:
                Command.run(
                    ['chroot', self.root_dir, 'dpkg', '-l', delete_item]
                )
                delete_items.append(delete_item)
            except Exception:
                # ignore packages which are not installed
                pass
        if not delete_items:
            raise KiwiRequestError(
                'None of the requested packages to delete are installed'
            )

        if force:
            apt_get_command = ['chroot', self.root_dir, 'dpkg']
            apt_get_command.extend(['--force-all', '-r'])
            apt_get_command.extend(delete_items)
        else:
            apt_get_command = ['chroot', self.root_dir, 'apt-get']
            apt_get_command.extend(
                Path.move_to_root(self.root_dir, self.apt_get_args)
            )
            apt_get_command.extend(self.custom_args)
            apt_get_command.extend(['--auto-remove', 'remove'])
            apt_get_command.extend(delete_items)

        return Command.call(
            apt_get_command, self.command_env
        )

    def update(self) -> command_call_type:
        """
        Process package update requests (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        apt_get_command = ['chroot', self.root_dir, 'apt-get']
        apt_get_command.extend(
            Path.move_to_root(self.root_dir, self.apt_get_args)
        )
        apt_get_command.extend(self.custom_args)
        apt_get_command.append('upgrade')

        return Command.call(
            apt_get_command, self.command_env
        )

    def process_only_required(self) -> None:
        """
        Setup package processing only for required packages
        """
        if '--no-install-recommends' not in self.custom_args:
            self.custom_args.append('--no-install-recommends')
        self.deboostrap_minbase = True

    def process_plus_recommended(self) -> None:
        """
        Setup package processing to also include recommended dependencies.
        """
        if '--no-install-recommends' in self.custom_args:
            self.custom_args.remove('--no-install-recommends')
        self.deboostrap_minbase = False

    def match_package_installed(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        """
        Match expression to indicate a package has been installed

        This match for the package to be installed in the output
        of the apt-get command is not 100% accurate. There might
        be false positives due to sub package names starting with
        the same base package name

        :param str package_name: package_name
        :param str package_manager_output: apt-get status line

        :returns: True|False

        :rtype: bool
        """
        return bool(
            re.match(
                '.*Unpacking {0}.*'.format(re.escape(package_name)),
                package_manager_output
            )
        )

    def match_package_deleted(
        self, package_name: str, package_manager_output: str
    ) -> bool:
        """
        Match expression to indicate a package has been deleted

        :param str package_name: package_name
        :param str package_manager_output: apt-get status line

        :returns: True|False

        :rtype: bool
        """
        return bool(
            re.match(
                '.*Removing {0}.*'.format(re.escape(package_name)),
                package_manager_output
            )
        )

    def _package_requests(self) -> List:
        items = self.package_requests[:]
        self.cleanup_requests()
        return items
