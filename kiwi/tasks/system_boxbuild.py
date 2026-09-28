# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from typing import List

# project
from kiwi.tasks.base import CliTask
from kiwi.help import Help
from kiwi.boxbuild.box_build import BoxBuild
from kiwi.boxbuild.box_container_build import BoxContainerBuild
from kiwi.boxbuild.boxes_config import BoxesConfig

from kiwi.exceptions import KiwiBoxBuildError

log = logging.getLogger('kiwi')


class SystemBoxbuildTask(CliTask):
    """
    Implements building of system images in a self contained
    virtual machine or container, called a box

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self) -> None:
        """
        Build a system image from the specified description in a box.
        The box runs the kiwi build command with the provided
        build command arguments
        """
        self.manual = Help()
        if self._help():
            return

        if self.command_args.get('--list-boxes'):
            print(BoxesConfig().dump_config())

        elif self.command_args.get('--box'):
            keep_open = bool(self.command_args.get('--box-debug'))
            kiwi_version = self.command_args.get('--kiwi-version')
            shared_path = self.command_args.get('--shared-path')

            if self.command_args.get('--container'):
                box_container_build = BoxContainerBuild(
                    boxname=self.command_args['--box'],
                    arch=self._get_box_arch()
                )
                box_container_build.run(
                    self._get_kiwi_build_command(),
                    keep_open,
                    kiwi_version,
                    shared_path
                )
            else:
                request_update_check = not self.command_args.get(
                    '--no-update-check'
                )
                request_snapshot_mode = not self.command_args.get(
                    '--no-snapshot'
                )
                box_build = BoxBuild(
                    boxname=self.command_args['--box'],
                    ram=self.command_args.get('--box-memory'),
                    console=self.command_args.get('--box-console'),
                    smp=self.command_args.get('--box-smp-cpus'),
                    arch=self._get_box_arch(),
                    machine=self.command_args.get('--machine'),
                    cpu=self.command_args.get('--cpu') or 'host',
                    sharing_backend=self._get_sharing_backend(),
                    ssh_key=self.command_args.get('--ssh-key') or 'id_rsa',
                    ssh_port=self.command_args.get('--ssh-port') or '',
                    accel=not bool(self.command_args.get('--no-accel'))
                )
                box_build.run(
                    self._get_kiwi_build_command(),
                    request_update_check,
                    request_snapshot_mode,
                    keep_open,
                    kiwi_version,
                    shared_path
                )

    def _help(self) -> bool:
        if self.command_args.get('help'):
            self.manual.show('kiwi::system::boxbuild')
            return True
        return False

    def _get_kiwi_build_command(self) -> List[str]:
        """
        Construct the kiwi system build command to run in the box
        from the global options and the arguments passed along with
        the kiwi subcommand of boxbuild
        """
        kiwi_build_command = [
            'system', 'build'
        ]
        translate_to_abspath = False
        for entry in self.command_args.get('system_build') or []:
            if translate_to_abspath:
                entry = os.path.abspath(os.path.normpath(entry))
                translate_to_abspath = False
            if entry == '--description' or entry == '--target-dir':
                translate_to_abspath = True
            kiwi_build_command.append(entry)

        final_kiwi_build_command = []
        if self.global_args.get('--debug'):
            final_kiwi_build_command.append('--debug')
        if self.global_args.get('--type'):
            final_kiwi_build_command.append('--type')
            final_kiwi_build_command.append(self.global_args.get('--type'))
        if self.global_args.get('--profile'):
            for profile in sorted(set(self.global_args.get('--profile'))):
                final_kiwi_build_command.append('--profile')
                final_kiwi_build_command.append(profile)
        if self.global_args.get('--kiwi-file'):
            final_kiwi_build_command.append('--kiwi-file')
            final_kiwi_build_command.append(self.global_args.get('--kiwi-file'))
        final_kiwi_build_command += kiwi_build_command
        missing_required_options = [
            option for option in ['--description', '--target-dir']
            if option not in final_kiwi_build_command
        ]
        if missing_required_options:
            raise KiwiBoxBuildError(
                'Required option(s) missing in kiwi build command: {0}'.format(
                    ', '.join(missing_required_options)
                )
            )
        log.info(
            'Building with:{0}    {1}'.format(
                os.linesep, final_kiwi_build_command
            )
        )
        return final_kiwi_build_command

    def _get_box_arch(self) -> str:
        box_arch = ''
        if self.command_args.get('--x86_64'):
            box_arch = 'x86_64'
        elif self.command_args.get('--aarch64'):
            box_arch = 'aarch64'
        return box_arch

    def _get_sharing_backend(self) -> str:
        if self.command_args.get('--virtiofs-sharing'):
            return 'virtiofs'
        if self.command_args.get('--sshfs-sharing'):
            return 'sshfs'
        return '9p'
