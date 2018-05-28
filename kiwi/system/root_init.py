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
from pwd import getpwnam
from tempfile import mkdtemp
from shutil import rmtree
from shutil import copy
import os

# project
from kiwi.utils.sync import DataSync
from kiwi.command import Command
from kiwi.path import Path
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiRootDirExists,
    KiwiRootInitCreationError
)


class RootInit(object):
    """
    **Implements creation of new root directory for a linux system**

    Host system independent static default files and device nodes
    are created to initialize a new base system

    :param str root_dir: root directory path name
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

        :raises KiwiRootInitCreationError: if the init creation fails
            at some point
        """
        root = mkdtemp(prefix='kiwi_root.')
        Path.create(self.root_dir)
        try:
            self._create_base_directories(root)
            self._create_base_links(root)
            self._setup_config_templates(root)
            data = DataSync(root + '/', self.root_dir)
            data.sync_data(
                options=['-a', '--ignore-existing']
            )
            if Defaults.is_buildservice_worker():
                copy(
                    os.sep + Defaults.get_buildservice_env_name(),
                    self.root_dir)
        except Exception as e:
            self.delete()
            raise KiwiRootInitCreationError(
                '%s: %s' % (type(e).__name__, format(e))
            )
        finally:
            rmtree(root, ignore_errors=True)

    def _setup_config_templates(self, root):
        group_template = '/var/adm/fillup-templates/group.aaa_base'
        passwd_template = '/var/adm/fillup-templates/passwd.aaa_base'
        proxy_template = '/var/adm/fillup-templates/sysconfig.proxy'
        if os.path.exists(group_template):
            Command.run(['cp', group_template, root + '/etc/group'])
        if os.path.exists(passwd_template):
            Command.run(['cp', passwd_template, root + '/etc/passwd'])
        if os.path.exists(proxy_template):
            Command.run(['cp', proxy_template, root + '/etc/sysconfig/proxy'])

    def _create_base_directories(self, root):
        """
        Create minimum collection of directories in the new
        root system required for kiwi to operate

        :param str root: path to the new root
        """
        base_system_paths = (
            Defaults.get_shared_cache_location(),
            'dev/pts',
            'proc',
            'etc/sysconfig',
            'run',
            'sys',
            'var'
        )
        root_uid = getpwnam('root').pw_uid
        root_gid = getpwnam('root').pw_gid
        for path in base_system_paths:
            root_path = os.sep.join([root, path])
            if not os.path.exists(root_path):
                os.makedirs(root_path)
                os.chown(root_path, root_uid, root_gid)

    def _create_base_links(self, root):
        """
        Create minimum collection of file handle and runtime
        links which needs to be present prior to any package
        installation

        :param str root: path to the new root
        """
        base_system_links = (
            ('/proc/self/fd', '%s/dev/fd'),
            ('fd/2', '%s/dev/stderr'),
            ('fd/0', '%s/dev/stdin'),
            ('fd/1', '%s/dev/stdout'),
            ('/run', '%s/var/run')
        )
        for src, target in base_system_links:
            os.symlink(src, target % root, )
