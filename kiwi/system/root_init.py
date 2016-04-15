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
from tempfile import mkdtemp
from shutil import rmtree
import os

# project
from ..utils.sync import DataSync
from ..command import Command
from ..path import Path

from ..exceptions import (
    KiwiRootDirExists,
    KiwiRootInitCreationError
)


class RootInit(object):
    """
    Implements creation of new root directory for a linux system.
    Host system independent static default files and device nodes
    are created to initialize a new base system

    Attributes

    * :attr:`root_dir`
        root directory path name
    """
    def __init__(self, root_dir, allow_existing=False):
        if not allow_existing and os.path.exists(root_dir):
            raise KiwiRootDirExists(
                'Root directory %s already exists' % root_dir
            )
        self.root_dir = root_dir

    def delete(self):
        """
        Force delete root directory and its contents
        """
        Path.wipe(self.root_dir)

    def create(self):
        """
        Create new system root directory

        The method creates a temporary directory and initializes it
        for the purpose of building a system image from it. This
        includes the following setup:

        * create static core device nodes
        * create core system paths

        On success the contents of the temporary location are
        synced to the specified root_dir and the temporary location
        will be deleted. That way we never work on an incomplete
        initial setup
        """
        root = mkdtemp()
        try:
            Path.create(root)
            base_system_paths = [
                '/dev/pts',
                '/proc',
                '/etc/sysconfig',
                '/var/cache',
                '/run',
                '/sys'
            ]
            for path in base_system_paths:
                Path.create(root + path)
                Command.run(['chown', 'root:root', root + path])

            Command.run(
                ['mknod', '-m', '666', root + '/dev/null', 'c', '1', '3']
            )
            Command.run(
                ['mknod', '-m', '666', root + '/dev/zero', 'c', '1', '5']
            )
            Command.run(
                ['mknod', '-m', '622', root + '/dev/full', 'c', '1', '7']
            )
            Command.run(
                ['mknod', '-m', '666', root + '/dev/random', 'c', '1', '8']
            )
            Command.run(
                ['mknod', '-m', '644', root + '/dev/urandom', 'c', '1', '9']
            )
            Command.run(
                ['mknod', '-m', '666', root + '/dev/tty', 'c', '5', '0']
            )
            Command.run(
                ['mknod', '-m', '666', root + '/dev/ptmx', 'c', '5', '2']
            )
            Command.run(
                ['mknod', '-m', '640', root + '/dev/loop0', 'b', '7', '0']
            )
            Command.run(
                ['mknod', '-m', '640', root + '/dev/loop1', 'b', '7', '1']
            )
            Command.run(
                ['mknod', '-m', '640', root + '/dev/loop2', 'b', '7', '2']
            )
            Command.run(
                ['mknod', '-m', '666', root + '/dev/loop3', 'b', '7', '3']
            )
            Command.run(
                ['mknod', '-m', '666', root + '/dev/loop4', 'b', '7', '4']
            )

            Command.run(['ln', '-s', '/proc/self/fd', root + '/dev/fd'])
            Command.run(['ln', '-s', 'fd/2', root + '/dev/stderr'])
            Command.run(['ln', '-s', 'fd/0', root + '/dev/stdin'])
            Command.run(['ln', '-s', 'fd/1', root + '/dev/stdout'])
            Command.run(['ln', '-s', '/run', root + '/var/run'])

            self.__setup_config_templates(root)
            data = DataSync(root + '/', self.root_dir)
            data.sync_data(
                options=['-a', '--ignore-existing']
            )
            Path.wipe(root)
        except Exception as e:
            rmtree(root, ignore_errors=True)
            raise KiwiRootInitCreationError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def __setup_config_templates(self, root):
        group_template = '/var/adm/fillup-templates/group.aaa_base'
        passwd_template = '/var/adm/fillup-templates/passwd.aaa_base'
        proxy_template = '/var/adm/fillup-templates/sysconfig.proxy'
        if os.path.exists(group_template):
            Command.run(['cp', group_template, root + '/etc/group'])
        if os.path.exists(passwd_template):
            Command.run(['cp', passwd_template, root + '/etc/passwd'])
        if os.path.exists(proxy_template):
            Command.run(['cp', proxy_template, root + '/etc/sysconfig/proxy'])
