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
import logging
import shutil
import textwrap
from typing import List

# project
from kiwi.command import Command
from kiwi.defaults import Defaults
from kiwi.path import Path
from kiwi.mount_manager import MountManager
from kiwi.utils.checksum import Checksum
from kiwi.system.root_init import RootInit

from kiwi.exceptions import (
    KiwiMountKernelFileSystemsError,
    KiwiMountSharedDirectoryError,
    KiwiSetupIntermediateConfigError
)

log = logging.getLogger('kiwi')


class RootBind:
    """
    **Implements binding/copying of host system paths
    into the new root directory**

    :param str root_dir: root directory path name
    :param list cleanup_files: list of files to cleanup, delete
    :param list mount_stack: list of mounted directories for cleanup
    :param list dir_stack: list of directories for cleanup
    :param list config_files: list of initial config files
    :param list bind_locations: list of kernel filesystems to bind mount
    :param str shared_location: shared directory between image root and
        build system root
    """
    def __init__(self, root_init: RootInit):
        self.root_dir = root_init.root_dir
        self.cleanup_files: List[str] = []
        self.mount_stack: List[MountManager] = []
        self.dir_stack: List[str] = []
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

    def mount_kernel_file_systems(self) -> None:
        """
        Bind mount kernel filesystems

        :raises KiwiMountKernelFileSystemsError: if some kernel filesystem
            fails to mount
        """
        try:
            for location in self.bind_locations:
                location_mount_target = os.path.normpath(os.sep.join([
                    self.root_dir, location
                ]))
                if os.path.exists(location) and os.path.exists(
                    location_mount_target
                ):
                    shared_mount = MountManager(
                        device=location, mountpoint=location_mount_target
                    )
                    shared_mount.bind_mount()
                    self.mount_stack.append(shared_mount)
        except Exception as e:
            self.cleanup()
            raise KiwiMountKernelFileSystemsError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def umount_kernel_file_systems(self) -> None:
        """
        Umount kernel filesystems

        :raises KiwiMountKernelFileSystemsError: if some kernel filesystem
            fails to mount
        """
        umounts = [
            mnt for mnt in self.mount_stack if mnt.device
            in self.bind_locations
        ]
        self._cleanup_mounts(umounts)

    def mount_shared_directory(self, host_dir: str = None) -> None:
        """
        Bind mount shared location

        The shared location is a directory which shares data from
        the image buildsystem host with the image root system. It
        is used for the repository setup and the package manager
        cache to allow chroot operations without being forced to
        duplicate this data

        :param str host_dir: directory to share between image root and build
            system root

        :raises KiwiMountSharedDirectoryError: if mount fails
        """
        if host_dir is None:
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

    def setup_intermediate_config(self) -> None:
        """
        Create intermediate config files

        Some config files e.g etc/hosts needs to be temporarly copied
        from the buildsystem host to the image root system in order to
        allow e.g DNS resolution in the way as it is configured on the
        buildsystem host. These config files only exists during the image
        build process and are not part of the final image

        :raises KiwiSetupIntermediateConfigError: if the management of
            intermediate configuration files fails
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
                    checksum = Checksum(config)
                    with open(self.root_dir + config + '.sha', 'w') as shasum:
                        shasum.write(checksum.sha256())
        except Exception as e:
            self.cleanup()
            raise KiwiSetupIntermediateConfigError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def cleanup(self) -> None:
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
            config_file = self.root_dir + config
            shasum_file = config_file.replace('.kiwi', '.sha')

            config_files_to_delete.append(config_file)
            config_files_to_delete.append(shasum_file)

            checksum = Checksum(config_file)
            if not checksum.matches(checksum.sha256(), shasum_file):
                message = textwrap.dedent('''\n
                    Modifications to intermediate config file detected

                    The file: {0}

                    is a copy from the host system and symlinked
                    to its origin in the image root during build time.
                    Modifications to this file by e.g script code will not
                    have any effect because the file gets restored by one
                    of the following actions:

                    1. A package during installation provides it
                    2. A custom version of the file is setup as overlay file
                    3. The file is not provided by install or overlay and will
                       be deleted at the end of the build process

                    If you need a custom version of that file please
                    provide it as an overlay file in your image
                    description
                ''')
                log.warning(message.format(config_file))

        del self.cleanup_files[:]

        # delete stale symlinks if there are any. normally the package
        # installation process should have replaced the symlinks with
        # real files from the packages. On deletion check for the
        # presence of a config file template and restore it
        try:
            for config in self.config_files:
                config_file = self.root_dir + config
                if os.path.islink(config_file):
                    Command.run(['rm', '-f', config_file])
                    self._restore_config_template(config_file)

            Command.run(['rm', '-f'] + config_files_to_delete)
        except Exception as issue:
            log.warning(
                'Failed to cleanup intermediate config files: {0}'.format(issue)
            )

        self._restore_intermediate_config_rpmnew_variants()

    def _restore_config_template(self, config_file):
        """
        Systems that use configuration templates and a tool to
        manage them might have skipped their call due to the
        presence of intermediate host config files in the new
        root tree. In this case if no custom file was provided
        the template file is used to restore the system standard
        configuration file
        """
        template_map = {
            self.root_dir + '/etc/sysconfig/proxy': 'sysconfig.proxy'
        }
        template_dirs = [
            self.root_dir + '/var/adm/fillup-templates',
            self.root_dir + '/usr/share/fillup-templates'
        ]
        if template_map.get(config_file):
            for template_dir in template_dirs:
                template_file = os.sep.join(
                    [template_dir, template_map.get(config_file)]
                )
                if os.path.exists(template_file):
                    Command.run(
                        ['cp', template_file, config_file]
                    )

    def _restore_intermediate_config_rpmnew_variants(self):
        """
        check for rpmnew variants of the config files. if the package
        installed an rpmnew variant of the config file it needs to be
        moved to the original file name
        """
        for config in self.config_files:
            config_rpm_new = self.root_dir + config + '.rpmnew'
            if os.path.exists(config_rpm_new) and not \
               os.path.exists(self.root_dir + config):

                shutil.move(config_rpm_new, self.root_dir + config)

    def _cleanup_mounts(self, umounts):
        for umount in reversed(umounts):
            if umount.is_mounted():
                try:
                    umount.umount_lazy()
                    self.mount_stack.remove(umount)
                except Exception as e:
                    log.warning(
                        'Image root directory %s not cleanly umounted: %s',
                        self.root_dir, format(e)
                    )
            else:
                log.warning('Path %s not a mountpoint', umount.mountpoint)

    def _cleanup_mount_stack(self):
        self._cleanup_mounts(self.mount_stack)
        del self.mount_stack[:]

    def _cleanup_dir_stack(self):
        for location in reversed(self.dir_stack):
            try:
                Path.remove_hierarchy(root=self.root_dir, path=location)
            except Exception as e:
                log.warning(
                    'Failed to remove directory hierarchy {0}: {1}'.format(
                        self.root_dir + location, e
                    )
                )
        del self.dir_stack[:]
