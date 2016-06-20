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
import os

# project
from ..command import Command
from ..defaults import Defaults
from ..logger import log
from ..path import Path
from ..mount_manager import MountManager

from ..exceptions import (
    KiwiMountKernelFileSystemsError,
    KiwiMountSharedDirectoryError,
    KiwiSetupIntermediateConfigError
)


class RootBind(object):
    """
    Implements binding/copying of host system paths
    into the new root directory

    Attributes

    * :attr:`root_dir`
        root directory path name

    * :attr:`cleanup_files`
        list of files to cleanup, delete

    * :attr:`mount_stack`
        list of mounted directories for cleanup

    * :attr:`dir_stack`
        list of directories for cleanup

    * :attr:`config_files`
        list of initial config files

    * :attr:`bind_locations`
        list of kernel filesystems to bind mount

    * :attr:`shared_location`
        shared directory between image root and build system root
    """
    def __init__(self, root_init):
        self.root_dir = root_init.root_dir
        self.cleanup_files = []
        self.mount_stack = []
        self.dir_stack = []
        # need resolv.conf/hosts for chroot name resolution
        # need /etc/sysconfig/proxy for chroot proxy usage
        self.config_files = [
            '/etc/resolv.conf',
            '/etc/hosts',
            '/etc/sysconfig/proxy'
        ]
        # need kernel filesystems bind mounted
        self.bind_locations = [
            '/proc',
            '/dev',
            '/var/run/dbus',
            '/sys'
        ]
        # share the following directory with the host
        self.shared_location = '/' + Defaults.get_shared_cache_location()

    def mount_kernel_file_systems(self):
        """
        Bind mount kernel filesystems
        """
        try:
            for location in self.bind_locations:
                if os.path.exists(location):
                    shared_mount = MountManager(
                        device=location, mountpoint=self.root_dir + location
                    )
                    shared_mount.bind_mount()
                    self.mount_stack.append(shared_mount)
        except Exception as e:
            self.cleanup()
            raise KiwiMountKernelFileSystemsError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def mount_shared_directory(self, host_dir=None):
        """
        Bind mount shared location

        The shared location is a directory which shares data from
        the image buildsystem host with the image root system. It
        is used for the repository setup and the package manager
        cache to allow chroot operations without being forced to
        duplicate this data
        """
        if not host_dir:
            host_dir = self.shared_location
        try:
            Path.create(self.root_dir + host_dir)
            Path.create('/' + host_dir)
            shared_mount = MountManager(
                device=host_dir, mountpoint=self.root_dir + host_dir
            )
            shared_mount.bind_mount()
            self.mount_stack.append(shared_mount)
            self.dir_stack.append(host_dir)
        except Exception as e:
            self.cleanup()
            raise KiwiMountSharedDirectoryError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def setup_intermediate_config(self):
        """
        Create intermediate config files

        Some config files e.g etc/hosts needs to be temporarly copied
        from the buildsystem host to the image root system in order to
        allow e.g DNS resolution in the way as it is configured on the
        buildsystem host. These config files only exists during the image
        build process and are not part of the final image
        """
        try:
            for config in self.config_files:
                if os.path.exists(config):
                    self.cleanup_files.append(config + '.kiwi')
                    Command.run(
                        ['cp', config, self.root_dir + config + '.kiwi']
                    )
                    link_target = os.path.basename(config) + '.kiwi'
                    Command.run(
                        ['ln', '-s', '-f', link_target, self.root_dir + config]
                    )
        except Exception as e:
            self.cleanup()
            raise KiwiSetupIntermediateConfigError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def move_to_root(self, elements):
        """
        Change the given path elements to a new root directory

        :param list elements: list of path names

        :return: changed elements
        :rtype: list
        """
        result = []
        for element in elements:
            normalized_element = os.path.normpath(element)
            result.append(
                normalized_element.replace(os.path.normpath(self.root_dir), '/')
            )
        return result

    def cleanup(self):
        """
        Cleanup mounted locations, directories and intermediate config files
        """
        self._cleanup_mount_stack()
        self._cleanup_dir_stack()
        self._cleanup_intermediate_config()

    def _cleanup_intermediate_config(self):
        # delete kiwi copied config files
        config_files_to_delete = []

        for config in self.cleanup_files:
            config_files_to_delete.append(self.root_dir + config)

        del self.cleanup_files[:]

        # delete stale symlinks if there are any. normally the package
        # installation process should have replaced the symlinks with
        # real files from the packages
        for config in self.config_files:
            if os.path.islink(self.root_dir + config):
                config_files_to_delete.append(self.root_dir + config)

        try:
            Command.run(['rm', '-f'] + config_files_to_delete)
        except Exception as e:
            log.warning(
                'Failed to remove intermediate config files: %s', format(e)
            )

    def _cleanup_mount_stack(self):
        for mount in reversed(self.mount_stack):
            if mount.is_mounted():
                try:
                    mount.umount_lazy()
                except Exception as e:
                    log.warning(
                        'Image root directory %s not cleanly umounted: %s',
                        self.root_dir, format(e)
                    )
            else:
                log.warning('Path %s not a mountpoint', mount.mountpoint)

        del self.mount_stack[:]

    def _cleanup_dir_stack(self):
        for location in reversed(self.dir_stack):
            try:
                Path.remove_hierarchy(self.root_dir + location)
            except Exception as e:
                log.warning(
                    'Failed to remove directory %s: %s', location, format(e)
                )
        del self.dir_stack[:]
