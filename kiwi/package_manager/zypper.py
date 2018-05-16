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
    **Implements base class for installation/deletion of
    packages and collections using zypper**

    :param list zypper_args: zypper arguments from repository runtime
        configuration
    :param dict command_env: zypper command environment from repository
        runtime configuration
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom zypper arguments

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

        :param str name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name):
        """
        Queue a collection request

        :param str name: zypper pattern name
        """
        self.collection_requests.append('pattern:' + name)

    def request_product(self, name):
        """
        Queue a product request

        :param str name: zypper product name
        """
        self.product_requests.append('product:' + name)

    def request_package_exclusion(self, name):
        """
        Queue a package exclusion(skip) request

        :param str name: package name
        """
        self.exclude_requests.append(name)

    def process_install_requests_bootstrap(self):
        """
        Process package install requests for bootstrap phase (no chroot)

        :return: process results in command type

        :rtype: namedtuple
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
                    ['chroot', self.root_dir, 'zypper'] +
                    self.chroot_zypper_args + ['al'] + [package],
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

        :raises KiwiRequestError: if none of the packages to delete is
            installed
        :return: process results in command type

        :rtype: namedtuple
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

        :return: process results in command type

        :rtype: namedtuple
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

    def process_plus_recommended(self):
        """
        Setup package processing to also include recommended dependencies.
        """
        if '--no-recommends' in self.custom_args:
            self.custom_args.remove('--no-recommends')

    def match_package_installed(self, package_name, zypper_output):
        """
        Match expression to indicate a package has been installed

        This match for the package to be installed in the output
        of the zypper command is not 100% accurate. There might
        be false positives due to sub package names starting with
        the same base package name

        :param list package_list: list of all packages
        :param str log_line: zypper status line

        :returns: match or None if there isn't any match

        :rtype: match object, None
        """
        return re.match(
            '.*Installing: ' + re.escape(package_name) + '.*', zypper_output
        )

    def match_package_deleted(self, package_name, zypper_output):
        """
        Match expression to indicate a package has been deleted

        :param list package_list: list of all packages
        :param str log_line: zypper status line

        :returns: match or None if there isn't any match

        :rtype: match object, None
        """
        return re.match(
            '.*Removing: ' + re.escape(package_name) + '.*', zypper_output
        )

    def database_consistent(self):
        """
        Check if rpm package database is consistent

        :return: True or False

        :rtype: bool
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

        :param str version: target rpm db version
        """
        db_load_for_version = {
            45: 'db45_load',
            48: 'db48_load'
        }

        rpmdb_path_request = Command.run(
            ['chroot', self.root_dir, 'rpm', '-E', '%_dbpath']
        )
        rpmdb_path = os.path.normpath(os.sep.join(
            [self.root_dir, rpmdb_path_request.output.strip()]
        ))
        if not os.path.exists(rpmdb_path):
            raise KiwiRpmDatabaseReloadError(
                'Unable to get the rpmdb location {0}'.format(rpmdb_path)
            )

        if version not in db_load_for_version:
            raise KiwiRpmDatabaseReloadError(
                'Dump reload for rpm DB version: %s not supported' % version
            )
        if not self.database_consistent():
            reload_db_files = [
                os.sep.join([rpmdb_path, 'Name']),
                os.sep.join([rpmdb_path, 'Packages'])
            ]
            for db_file in reload_db_files:
                db_file_backup = '{0}.bak'.format(db_file)
                Command.run([
                    'db_dump', '-f', db_file_backup, db_file
                ])
                Command.run(['rm', '-f', db_file])
                Command.run([
                    db_load_for_version[version],
                    '-f', db_file_backup, db_file
                ])
                Command.run(['rm', '-f', db_file_backup])
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
