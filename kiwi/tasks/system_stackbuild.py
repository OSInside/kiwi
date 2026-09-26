# Copyright (c) 2021 SUSE Linux GmbH.  All rights reserved.
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
import sys
import logging
from unittest.mock import patch
from typing import List

# project
from kiwi.help import Help
from kiwi.privileges import Privileges
from kiwi.tasks.base import CliTask
from kiwi.tasks.system_create import SystemCreateTask
from kiwi.tasks.system_build import SystemBuildTask
from kiwi.command import Command
from kiwi.path import Path
from kiwi.utils.sync import DataSync
from kiwi.defaults import Defaults

from kiwi.exceptions import (
    KiwiStackBuildTargetDirExists,
    KiwiStackBuildRootSyncFailed
)

log = logging.getLogger('kiwi')


class SystemStackbuildTask(CliTask):
    """
    Implements building of system images based on one or more
    stash containers stacked together as the image root tree

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self) -> None:
        """
        Sync the given stash containers into the image root tree
        and run the kiwi build command if a description is given,
        or the kiwi create command to rebuild from the stash
        """
        self.manual = Help()
        if self.command_args.get('help') is True:
            return self.manual.show('kiwi::system::stackbuild')

        Privileges.check_for_root_permissions()

        if self.command_args.get('--stash'):
            image_root_dir = os.path.join(
                self.command_args['--target-dir'], 'build', 'image-root'
            )
            if os.path.exists(image_root_dir):
                raise KiwiStackBuildTargetDirExists(
                    f'image root dir: {image_root_dir!r} already exists'
                )
            Path.create(image_root_dir)

            for stash_name in self.command_args['--stash']:
                if self.command_args.get('--from-registry'):
                    log.info(
                        'Fetching stash {0!r} from registry {1!r}'.format(
                            stash_name,
                            self.command_args['--from-registry']
                        )
                    )
                    Command.run(
                        [
                            'podman', 'pull', os.path.join(
                                self.command_args['--from-registry'],
                                stash_name
                            )
                        ]
                    )
                try:
                    log.info(f'Mounting stash: {stash_name!r}')
                    stash_mount_point = Command.run(
                        ['podman', 'image', 'mount', stash_name]
                    ).output.strip()
                    root = DataSync(
                        stash_mount_point + os.sep, image_root_dir
                    )
                    log.info(
                        'Syncing stash root {0!r} to image root {1!r}'.format(
                            stash_mount_point, image_root_dir
                        )
                    )
                    root.sync_data(
                        options=Defaults.get_sync_options()
                    )
                except Exception as issue:
                    raise KiwiStackBuildRootSyncFailed(issue)
                finally:
                    log.info(f'Umount stash: {stash_name!r}')
                    Command.run(
                        ['podman', 'image', 'umount', '--force', stash_name],
                        raise_on_error=False
                    )

            kiwi_task: CliTask
            if self.command_args.get('--description'):
                with patch.object(
                    sys, 'argv', self._get_kiwi_command(
                        [
                            'system', 'build',
                            '--description', self.command_args['--description'],
                            '--target-dir', self.command_args['--target-dir'],
                            '--allow-existing-root'
                        ]
                    )
                ):
                    kiwi_task = SystemBuildTask(
                        should_perform_task_setup=False
                    )
            else:
                with patch.object(
                    sys, 'argv', self._get_kiwi_command(
                        [
                            'system', 'create',
                            '--root', image_root_dir,
                            '--target-dir', self.command_args['--target-dir']
                        ]
                    )
                ):
                    kiwi_task = SystemCreateTask(
                        should_perform_task_setup=False
                    )

            kiwi_task.process()

    def _get_kiwi_command(self, kiwi_command: List[str]) -> List[str]:
        """
        Construct the kiwi build or create command from the global
        options, the given command and the arguments passed along
        with the kiwi subcommand of stackbuild
        """
        final_kiwi_command = ['kiwi-ng']
        if self.global_args.get('--type'):
            final_kiwi_command.append('--type')
            final_kiwi_command.append(self.global_args.get('--type'))
        if self.global_args.get('--profile'):
            for profile in sorted(set(self.global_args.get('--profile'))):
                final_kiwi_command.append('--profile')
                final_kiwi_command.append(profile)
        if self.global_args.get('--kiwi-file'):
            final_kiwi_command.append('--kiwi-file')
            final_kiwi_command.append(self.global_args.get('--kiwi-file'))
        final_kiwi_command += kiwi_command
        final_kiwi_command += \
            self.command_args.get('system_build_or_create') or []
        log.debug(
            'Building with:{0}    {1}'.format(
                os.linesep, final_kiwi_command
            )
        )
        return final_kiwi_command
