# Copyright (c) 2019 SUSE Linux GmbH.  All rights reserved.
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

# project
from kiwi.command import Command
from kiwi.package_manager.base import PackageManagerBase
from kiwi.exceptions import KiwiRequestError
from kiwi.path import Path

log = logging.getLogger('kiwi')


class PackageManagerPacman(PackageManagerBase):
    """
    **Implements base class for installation/deletion of
    packages and collections using pacman**

    :param list pacman_args: pacman arguments from repository runtime
        configuration
    :param dict command_env: pacman command environment from repository
        runtime configuration
    """
    def post_init(self, custom_args=None):
        """
        Post initialization method

        Store custom pacman arguments

        :param list custom_args: custom pacman arguments
        """
        self.custom_args = custom_args
        if not custom_args:
            self.custom_args = []

        runtime_config = self.repository.runtime_config()
        self.pacman_args = runtime_config['pacman_args']
        self.command_env = runtime_config['command_env']

    def request_package(self, name):
        """
        Queue a package request

        :param str name: package name
        """
        self.package_requests.append(name)

    def request_collection(self, name):
        """
        Queue a collection request

        Pacman does not distinguish the installation of pacakges
        and collections. Because of that collections are listed together
        with package requests and a warning message is shown.
        :param str name: pacman group name
        """
        log.warning((
            'Pacman treats collection installations as regular packages.'
            'It is preferred to list them as regular packages'
        ))
        self.package_requests.append(name)

    def request_product(self, name):
        """
        Queue a product request

        There is no product definition in the Arch Linux repo data

        :param str name: unused
        """
        pass

    def request_package_exclusion(self, name):
        """
        Queue a package exclusion(skip) request

        :param str name: package name
        """
        self.exclude_requests.append(name)

    def process_install_requests_bootstrap(self, root_bind=None):
        """
        Process package install requests for bootstrap phase (no chroot)

        :param object root_binf: unused

        :return: process results in command type

        :rtype: namedtuple
        """
        Command.run(
            ['pacman'] + self.pacman_args + [
                '--root', self.root_dir, '-Sy'
            ]
        )
        bash_command = [
            'pacman'
        ] + self.pacman_args + [
            '--root', self.root_dir
        ] + self.custom_args + [
            '-S', '--needed',
            '--overwrite', '{}/var/run'.format(self.root_dir)
        ] + self.package_requests
        self.cleanup_requests()
        return Command.call(
            ['bash', '-c', ' '.join(bash_command)], self.command_env
        )

    def process_install_requests(self):
        """
        Process package install requests for image phase (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        chroot_pacman_args = Path.move_to_root(self.root_dir, self.pacman_args)
        bash_command = [
            'chroot', self.root_dir, 'pacman'
        ] + chroot_pacman_args + self.custom_args + [
            '-S', '--needed'
        ] + self.package_requests
        self.cleanup_requests()
        return Command.call(
            ['bash', '-c', ' '.join(bash_command)], self.command_env
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
        for delete_item in self.package_requests:
            try:
                Command.run(['chroot', self.root_dir, 'pacman', '-Qi', delete_item])
                delete_items.append(delete_item)
            except Exception:
                # ignore packages which are not installed
                pass
        if not delete_items:
            raise KiwiRequestError(
                'None of the requested packages to delete are installed'
            )
        self.cleanup_requests()
        chroot_pacman_args = Path.move_to_root(self.root_dir, self.pacman_args)
        return Command.call(
            [
                'chroot', self.root_dir, 'pacman'
            ] + chroot_pacman_args + self.custom_args + [
                '-Rdd' if force else '-Rs'
            ] + delete_items,
            self.command_env
        )

    def update(self):
        """
        Process package update requests (chroot)

        :return: process results in command type

        :rtype: namedtuple
        """
        chroot_pacman_args = Path.move_to_root(self.root_dir, self.pacman_args)
        return Command.call(
            [
                'chroot', self.root_dir, 'pacman'
            ] + chroot_pacman_args + self.custom_args + [
                '-Su'
            ],
            self.command_env
        )

    def process_only_required(self):
        """
        Setup package processing only for required packages.

        This is the only option in pacman, nothing to do here.
        """
        pass

    def process_plus_recommended(self):
        """
        Setup package processing to also include recommended dependencies.

        There is no such concept of recommended dependencies in pacman.
        """
        pass

    def match_package_installed(self, package_name, pacman_output):
        """
        Match expression to indicate a package has been installed

        This match for the package to be installed in the output
        of the pacman command is not 100% accurate. There might
        be false positives due to sub package names starting with
        the same base package name

        :param list package_list: list of all packages
        :param str log_line: dnf status line

        :returns: match or None if there isn't any match

        :rtype: match object, None
        """
        return re.match(
            '.* installing ' + re.escape(package_name) + '.*', pacman_output
        )

    def match_package_deleted(self, package_name, pacman_output):
        """
        Match expression to indicate a package has been deleted

        :param list package_list: list of all packages
        :param str log_line: pacman status line

        :returns: match or None if there isn't any match

        :rtype: match object, None
        """
        return re.match(
            '.* removing ' + re.escape(package_name) + '.*', pacman_output
        )
