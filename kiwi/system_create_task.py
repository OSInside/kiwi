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
"""
usage: kiwi system create -h | --help
       kiwi system create --root=<directory> --target-dir=<directory>
       kiwi system create help

commands:
    create
        create a system image from the specified root directory
        the root directory is the result of a system prepare
        command
    create help
        show manual page for create command

options:
    --root=<directory>
        the path to the root directory, usually the result of
        a former system prepare call
    --target-dir=<directory>
        the target directory to store the system image file(s)
"""
import os

# project
from cli_task import CliTask
from help import Help
from defaults import Defaults
from archive_builder import ArchiveBuilder
from filesystem_builder import FileSystemBuilder
from container_builder import ContainerBuilder
from disk_builder import DiskBuilder
from live_image_builder import LiveImageBuilder
from pxe_builder import PxeBuilder
from privileges import Privileges
from path import Path

from exceptions import (
    KiwiRequestedTypeError,
    KiwiNotImplementedError
)


class SystemCreateTask(CliTask):
    """
        Implements creation of system images
    """
    def process(self):
        self.manual = Help()
        if self.__help():
            return

        Privileges.check_for_root_permissions()

        self.load_xml_description(
            self.command_args['--root']
        )

        result = None
        if self.command_args['create']:
            if not os.path.exists(self.command_args['--target-dir']):
                Path.create(self.command_args['--target-dir'])

            requested_image_type = self.xml_state.get_build_type_name()
            if requested_image_type in Defaults.get_filesystem_image_types():
                filesystem = FileSystemBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    self.command_args['--root']
                )
                result = filesystem.create()
            elif requested_image_type in Defaults.get_disk_image_types():
                disk = DiskBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    self.command_args['--root']
                )
                result = disk.create()
            elif requested_image_type in Defaults.get_live_image_types():
                live_iso = LiveImageBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    self.command_args['--root']
                )
                result = live_iso.create()
            elif requested_image_type in Defaults.get_network_image_types():
                pxe = PxeBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    self.command_args['--root']
                )
                result = pxe.create()
            elif requested_image_type in Defaults.get_archive_image_types():
                archive = ArchiveBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    self.command_args['--root']
                )
                result = archive.create()
            elif requested_image_type in Defaults.get_container_image_types():
                container = ContainerBuilder(
                    self.xml_state,
                    self.command_args['--target-dir'],
                    self.command_args['--root']
                )
                result = container.create()
            else:
                raise KiwiRequestedTypeError(
                    'requested image type %s not supported' %
                    requested_image_type
                )

            if result:
                result.print_results()
                result.dump(
                    self.command_args['--target-dir'] + '/kiwi.result'
                )

    def __help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::create')
        else:
            return False
        return self.manual
