# Copyright (c) 2025 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from typing import (
    List, Optional, NamedTuple
)

# project
from kiwi.mount_manager import MountManager
from kiwi.command import (
    Command, CommandT, MutableMapping
)
from kiwi.exceptions import (
    KiwiUmountBusyError
)

log = logging.getLogger('kiwi')


class ChrootMount(NamedTuple):
    target: str
    source: Optional[str] = None


class ChrootManager:
    """
    **Implements methods for setting and unsetting a chroot environment**

    The caller is responsible for cleaning up bind mounts if the ChrootManager
    is used as is, without a context.

    The class also supports to be used as a context manager, where any bind or kernel
    filesystem mount is unmounted once the context manager's with block is left

    * :param string root_dir: path to change the root to
    * :param list binds: current root paths to bind to the chrooted path
    """
    def __init__(self, root_dir: str, binds: List[ChrootMount] = []):
        self.root_dir = root_dir
        self.mounts: List[MountManager] = []
        for bind in binds:
            self.mounts.append(MountManager(
                device=bind.source if bind.source else bind.target,
                mountpoint=os.path.normpath(
                    os.sep.join([root_dir, bind.target])
                )
            ))

    def __enter__(self) -> "ChrootManager":
        try:
            self.mount()
        except Exception as e:
            try:
                self.umount()
            except Exception:
                pass
            raise e
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.umount()

    def mount(self) -> None:
        """
        Mounts binds to the chroot path
        """
        for mnt in self.mounts:
            mnt.bind_mount()

    def umount(self) -> None:
        """
        Unmounts all binds from the chroot path

        If any unmount raises a KiwiUmountBusyError this is trapped
        and kept until the iteration over all bind mounts is over.
        """
        errors = []
        for mnt in reversed(self.mounts):
            try:
                mnt.umount()
            except KiwiUmountBusyError as e:
                errors.append(e)

        if errors:
            raise KiwiUmountBusyError(errors)

    def run(
        self, command: List[str],
        custom_env: Optional[MutableMapping[str, str]] = None,
        raise_on_error: bool = True, stderr_to_stdout: bool = False,
        raise_on_command_not_found: bool = True
    ) -> Optional[CommandT]:
        """
        This is a wrapper for Command.run method but pre-appending the
        chroot call at the command list

        :param list command: command and arguments
        :param dict custom_env: custom os.environ
        :param bool raise_on_error: control error behaviour
        :param bool stderr_to_stdout: redirects stderr to stdout

        :return:
            Contains call results in command type

            .. code:: python

                CommandT(output='string', error='string', returncode=int)

        :rtype: CommandT
        """
        chroot_cmd = ['chroot', self.root_dir]
        chroot_cmd = chroot_cmd + command
        return Command.run(
            chroot_cmd, custom_env, raise_on_error, stderr_to_stdout,
            raise_on_command_not_found
        )
