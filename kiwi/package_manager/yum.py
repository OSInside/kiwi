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

# project
from ..command import Command
from .base import PackageManagerBase
from ..exceptions import (
    KiwiRequestError
)


class PackageManagerYum(PackageManagerBase):
    """
        Implements install tasks for the yum package manager
    """
    def post_init(self, custom_args=None):
        self.custom_args = custom_args
        if not custom_args:
            self.custom_args = []

        runtime_config = self.repository.runtime_config()
        self.yum_args = runtime_config['yum_args']
        self.command_env = runtime_config['command_env']

    def request_package(self, name):
        self.package_requests.append(name)

    def request_collection(self, name):
        self.collection_requests.append(name)

    def request_product(self, name):
        # There is no product definition in the rhel repo data
        pass

    def process_install_requests_bootstrap(self):
        Command.run(
            ['yum'] + self.yum_args + ['makecache']
        )
        bash_command = [
            'yum'
        ] + self.yum_args + [
            '--installroot', self.root_dir
        ] + self.custom_args + ['install'] + self.package_requests
        if self.collection_requests:
            bash_command += [
                '&&', 'yum'
            ] + self.yum_args + [
                '--installroot', self.root_dir
            ] + self.custom_args + ['groupinstall'] + self.collection_requests
        self.cleanup_requests()
        return Command.call(
            ['bash', '-c', ' '.join(bash_command)], self.command_env
        )

    def process_install_requests(self):
        Command.run(
            ['chroot', self.root_dir, 'rpm', '--rebuilddb']
        )
        chroot_yum_args = self.root_bind.move_to_root(
            self.yum_args
        )
        bash_command = [
            'chroot', self.root_dir, 'yum'
        ] + chroot_yum_args + self.custom_args + [
            'install'
        ] + self.package_requests
        if self.collection_requests:
            bash_command += [
                '&&', 'chroot', self.root_dir, 'yum'
            ] + chroot_yum_args + self.custom_args + [
                'groupinstall'
            ] + self.collection_requests
        self.cleanup_requests()
        return Command.call(
            ['bash', '-c', ' '.join(bash_command)], self.command_env
        )

    def process_delete_requests(self, force=False):
        delete_items = []
        for delete_item in self.package_requests:
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
        delete_options = ['--nodeps', '--allmatches', '--noscripts']
        self.cleanup_requests()
        return Command.call(
            [
                'chroot', self.root_dir, 'rpm', '-e'
            ] + delete_options + delete_items,
            self.command_env
        )

    def update(self):
        chroot_yum_args = self.root_bind.move_to_root(
            self.yum_args
        )
        return Command.call(
            [
                'chroot', self.root_dir, 'yum'
            ] + chroot_yum_args + self.custom_args + [
                'upgrade'
            ],
            self.command_env
        )

    def process_only_required(self):
        # There is no required/recommends information in the rhel repo data
        pass

    def match_package_installed(self, package_name, yum_output):
        # this match for the package to be installed in the output
        # of the yum command is not 100% accurate. There might
        # be false positives due to sub package names starting with
        # the same base package name
        return re.match(
            '.*Installing : ' + re.escape(package_name) + '.*', yum_output
        )

    def match_package_deleted(self, package_name, yum_output):
        return re.match(
            '.*Removing: ' + re.escape(package_name) + '.*', yum_output
        )

    def database_consistent(self):
        try:
            Command.run(['chroot', self.root_dir, 'rpmdb', '--initdb'])
            return True
        except Exception:
            return False

    def dump_reload_package_database(self, version=45):
        # For the versions of rhel we support there is no
        # dump/reload cycle required
        pass
