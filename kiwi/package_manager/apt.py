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

# project
from kiwi.command import Command
from kiwi.mount_manager import MountManager
from kiwi.logger import log
from kiwi.utils.sync import DataSync
from kiwi.path import Path
from kiwi.package_manager.base import PackageManagerBase
from kiwi.exceptions import (
    KiwiDebootstrapError,
    KiwiRequestError
)


class PackageManagerApt(PackageManagerBase):
    """
    **Implements base class for installation/deletion of
    packages and collections using apt-get**

    :param list apt_get_args: apt-get arguments from repository runtime
        configuration
    :param dict command_env: apt-get command environment from repository
        runtime configuration
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom apt-get arguments

        :param list custom_args: custom apt-get arguments
        """
        self.custom_args = custom_args
        if not custom_args:
            self.custom_args = []
        self.deboostrap_minbase = True

        runtime_config = self.repository.runtime_config()
        self.apt_get_args = runtime_config['apt_get_args']
        self.command_env = runtime_config['command_env']
        self.distribution = runtime_config['distribution']
        self.distribution_path = runtime_config['distribution_path']

    def request_package(self, name):
        """
        Queue a package request

        :param str name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name):
        """
        Queue a collection request

        There is no collection definition in the deb repo data

        :param str name: unused
        """
        log.warning(
            'Collection(%s) handling not supported for apt-get', name
        )

    def request_product(self, name):
        """
        Queue a product request

        There is no product definition in the deb repo data

        :param str name: unused
        """
        log.warning(
            'Product(%s) handling not supported for apt-get', name
        )

    def request_package_exclusion(self, name):
        """
        Queue a package exclusion(skip) request

        Package exclusion for apt package manager not yet implemented

        :param str name: unused
        """
        log.warning(
            'Package exclusion for (%s) not supported for apt-get', name
        )

    def process_install_requests_bootstrap(self):
        """
        Process package install requests for bootstrap phase (no chroot)
        The debootstrap program is used to bootstrap a new system with
        a collection of predefined packages. The kiwi bootstrap section
        information is not used in this case

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
        bootstrap_dir = self.root_dir + '.debootstrap'
        if 'apt-get' in self.package_requests:
            # debootstrap takes care to install apt-get
            self.package_requests.remove('apt-get')
        try:
            dev_mount = MountManager(
                device='/dev', mountpoint=self.root_dir + '/dev'
            )
            dev_mount.umount()
            if self.repository.unauthenticated == 'false':
                log.warning(
                    'KIWI does not support signature checks for apt-get '
                    'package manager during the bootstrap procedure, any '
                    'provided key will only be used inside the chroot '
                    'environment'
                )
            cmd = ['debootstrap', '--no-check-gpg']
            if self.deboostrap_minbase:
                cmd.append('--variant=minbase')
            cmd.extend([
                self.distribution, bootstrap_dir, self.distribution_path
            ])
            Command.run(cmd, self.command_env)
            data = DataSync(
                bootstrap_dir + '/', self.root_dir
            )
            data.sync_data(
                options=['-a', '-H', '-X', '-A']
            )
            for key in self.repository.signing_keys:
                Command.run([
                    'chroot', self.root_dir, 'apt-key', 'add', key
                ], self.command_env)
        except Exception as e:
            raise KiwiDebootstrapError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        finally:
            Path.wipe(bootstrap_dir)

        return self.process_install_requests()

    def process_install_requests(self):
        """
        Process package install requests for image phase (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        update_command = ['chroot', self.root_dir, 'apt-get']
        update_command.extend(self.root_bind.move_to_root(self.apt_get_args))
        update_command.extend(self.custom_args)
        update_command.append('update')
        Command.run(update_command, self.command_env)

        apt_get_command = ['chroot', self.root_dir, 'apt-get']
        apt_get_command.extend(self.root_bind.move_to_root(self.apt_get_args))
        apt_get_command.extend(self.custom_args)
        apt_get_command.append('install')
        apt_get_command.extend(self._package_requests())

        return Command.call(
            apt_get_command, self.command_env
        )

    def process_delete_requests(self, force=False):
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
                self.root_bind.move_to_root(self.apt_get_args)
            )
            apt_get_command.extend(self.custom_args)
            apt_get_command.extend(['--auto-remove', 'remove'])
            apt_get_command.extend(delete_items)

        return Command.call(
            apt_get_command, self.command_env
        )

    def update(self):
        """
        Process package update requests (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        apt_get_command = ['chroot', self.root_dir, 'apt-get']
        apt_get_command.extend(self.root_bind.move_to_root(self.apt_get_args))
        apt_get_command.extend(self.custom_args)
        apt_get_command.append('upgrade')

        return Command.call(
            apt_get_command, self.command_env
        )

    def process_only_required(self):
        """
        Setup package processing only for required packages
        """
        if '--no-install-recommends' not in self.custom_args:
            self.custom_args.append('--no-install-recommends')
        self.deboostrap_minbase = True

    def process_plus_recommended(self):
        """
        Setup package processing to also include recommended dependencies.
        """
        if '--no-install-recommends' in self.custom_args:
            self.custom_args.remove('--no-install-recommends')
        self.deboostrap_minbase = False

    def match_package_installed(self, package_name, apt_get_output):
        """
        Match expression to indicate a package has been installed

        This match for the package to be installed in the output
        of the apt-get command is not 100% accurate. There might
        be false positives due to sub package names starting with
        the same base package name

        :param list package_list: list of all packages
        :param str log_line: apt-get status line

        :returns: match or None if there isn't any match

        :rtype: match object, None
        """
        return re.match(
            '.*Unpacking ' + re.escape(package_name) + '.*', apt_get_output
        )

    def match_package_deleted(self, package_name, apt_get_output):
        """
        Match expression to indicate a package has been deleted

        :param list package_list: list of all packages
        :param str log_line: apt-get status line

        :returns: match or None if there isn't any match

        :rtype: match object, None
        """
        return re.match(
            '.*Removing ' + re.escape(package_name) + '.*', apt_get_output
        )

    def database_consistent(self):
        """
        Check if package database is consistent

        There is no database consistency/rebuild for apt-get
        """
        pass

    def dump_reload_package_database(self, version=45):
        """
        Dump and reload the package database to match the desired db version

        There is no such reload cycle for apt-get

        :param str version: unused
        """
        pass

    def _package_requests(self):
        items = self.package_requests[:]
        self.cleanup_requests()
        return items
