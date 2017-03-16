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
from kiwi.package_manager.base import PackageManagerBase
from kiwi.path import Path
from kiwi.exceptions import (
    KiwiRpmDatabaseReloadError,
    KiwiRequestError
)


class PackageManagerZypper(PackageManagerBase):
    """
    Implements base class for installation/deletion of
    packages and collections using zypper
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom zypper arguments

        Attributes

        * :attr:`zypper_args`
            zypper arguments from repository runtime configuration

        * :attr:`command_env`
            zypper command environment from repository runtime configuration

        :param list custom_args: custom zypper arguments
        """
        self.custom_args = custom_args
        if not custom_args:
            self.custom_args = []

        runtime_config = self.repository.runtime_config()

        self.zypper_args = runtime_config['zypper_args']
        self.chroot_zypper_args = self.root_bind.move_to_root(
            self.zypper_args
        )

        self.command_env = runtime_config['command_env']
        self.chroot_command_env = dict(self.command_env)
        if 'ZYPP_CONF' in self.command_env:
            self.chroot_command_env['ZYPP_CONF'] = self.root_bind.move_to_root(
                [self.command_env['ZYPP_CONF']]
            )[0]

    def request_package(self, name):
        """
        Queue a package request

        :param string name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name):
        """
        Queue a collection request

        :param string name: zypper pattern name
        """
        self.collection_requests.append('pattern:' + name)

    def request_product(self, name):
        """
        Queue a product request

        :param string name: zypper product name
        """
        self.product_requests.append('product:' + name)

    def request_package_lock(self, name):
        """
        Queue a package lock(ignore) request

        :param string name: package name
        """
        self.lock_requests.append(name)

    def process_install_requests_bootstrap(self):
        """
        Process package install requests for bootstrap phase (no chroot)
        """
        command = ['zypper'] + self.zypper_args + [
            '--root', self.root_dir,
            'install', '--auto-agree-with-licenses'
        ] + self.custom_args + self._install_items()
        return Command.call(
            command, self.command_env
        )

    def process_install_requests(self):
        """
        Process package install requests for image phase (chroot)
        """
        if self.lock_requests:
            # Zypper supports the package lock via the zypper al command
            # This allows to block a package from being taken into
            # consideration when the dependency solver runs. However
            # the request might be ignored by the package manager if
            # the lock request conflicts with a required package
            # dependency. e.g setting a lock on the glibc package will
            # for sure not work in order to keep the system in a
            # consistent state. Thus such lock requests are primarily
            # for packages pulled in by a recommendation but not by a
            # hard requirement.
            lock_metadata_dir = ''.join([self.root_dir, '/etc/zypp'])
            if not os.path.exists(lock_metadata_dir):
                Path.create(lock_metadata_dir)
            for package in self.lock_requests:
                Command.run(
                    [
                        'chroot', self.root_dir, 'zypper'
                    ] + self.chroot_zypper_args + [
                        'al'
                    ] + self.custom_args + [package],
                    self.chroot_command_env
                )
        return Command.call(
            ['chroot', self.root_dir, 'zypper'] + self.chroot_zypper_args + [
                'install', '--auto-agree-with-licenses'
            ] + self.custom_args + self._install_items(),
            self.chroot_command_env
        )

    def process_delete_requests(self, force=False):
        """
        Process package delete requests (chroot)

        :param bool force: force deletion: true|false
        """
        delete_items = []
        for delete_item in self._delete_items():
            try:
                Command.run(['chroot', self.root_dir, 'rpm', '-q', delete_item])
                delete_items.append(delete_item)
            except Exception:
                # ignore packages which are not installed
                pass
        if not delete_items:
            raise KiwiRequestError(
                'None of the requested packages to delete are installed'
            )
        if force:
            force_options = ['--nodeps', '--allmatches', '--noscripts']
            return Command.call(
                [
                    'chroot', self.root_dir, 'rpm', '-e'
                ] + force_options + delete_items,
                self.chroot_command_env
            )
        else:
            return Command.call(
                [
                    'chroot', self.root_dir, 'zypper'
                ] + self.chroot_zypper_args + [
                    'remove', '-u', '--force-resolution'
                ] + delete_items,
                self.chroot_command_env
            )

    def update(self):
        """
        Process package update requests (chroot)
        """
        return Command.call(
            ['chroot', self.root_dir, 'zypper'] + self.chroot_zypper_args + [
                'update', '--auto-agree-with-licenses'
            ] + self.custom_args,
            self.chroot_command_env
        )

    def process_only_required(self):
        """
        Setup package processing only for required packages
        """
        if '--no-recommends' not in self.custom_args:
            self.custom_args.append('--no-recommends')

    def match_package_installed(self, package_name, zypper_output):
        """
        Match expression to indicate a package has been installed

        This match for the package to be installed in the output
        of the zypper command is not 100% accurate. There might
        be false positives due to sub package names starting with
        the same base package name

        :param list package_list: list of all packages
        :param string log_line: zypper status line
        """
        return re.match(
            '.*Installing: ' + re.escape(package_name) + '.*', zypper_output
        )

    def match_package_deleted(self, package_name, zypper_output):
        """
        Match expression to indicate a package has been deleted

        :param list package_list: list of all packages
        :param string log_line: zypper status line
        """
        return re.match(
            '.*Removing: ' + re.escape(package_name) + '.*', zypper_output
        )

    def database_consistent(self):
        """
        Check if rpm package database is consistent
        """
        try:
            Command.run(['chroot', self.root_dir, 'rpmdb', '--initdb'])
            return True
        except Exception:
            return False

    def dump_reload_package_database(self, version=45):
        """
        Dump and reload the rpm database to match the desired rpm db version
        Supported target rpm database db versions are

        * 45 (db45_load)
        * 48 (db48_load)

        :param string version: target rpm db version
        """
        db_load_for_version = {
            45: 'db45_load',
            48: 'db48_load'
        }
        if version not in db_load_for_version:
            raise KiwiRpmDatabaseReloadError(
                'Dump reload for rpm DB version: %s not supported' % version
            )
        if not self.database_consistent():
            reload_db_files = [
                '/var/lib/rpm/Name',
                '/var/lib/rpm/Packages'
            ]
            for db_file in reload_db_files:
                root_db_file = self.root_dir + db_file
                root_db_file_backup = root_db_file + '.bak'
                Command.run([
                    'db_dump', '-f', root_db_file_backup, root_db_file
                ])
                Command.run(['rm', '-f', root_db_file])
                Command.run([
                    db_load_for_version[version],
                    '-f', root_db_file_backup, root_db_file
                ])
                Command.run(['rm', '-f', root_db_file_backup])
            Command.run([
                'chroot', self.root_dir, 'rpm', '--rebuilddb'
            ])

    def _install_items(self):
        items = self.package_requests + self.collection_requests \
            + self.product_requests
        self.cleanup_requests()
        return items

    def _delete_items(self):
        # collections and products can't be deleted
        items = []
        items += self.package_requests
        self.cleanup_requests()
        return items
