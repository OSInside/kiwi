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
usage: kiwi-ng system update -h | --help
       kiwi-ng system update --root=<directory>
           [--add-package=<name>...]
           [--delete-package=<name>...]
       kiwi-ng system update help

commands:
    update
        update root system with latest repository updates
        and optionally allow to add or delete packages. the options
        to add or delete packages can be used multiple times
    update help
        show manual page for update command

options:
    --add-package=<name>
        install the given package name
    --delete-package=<name>
        delete the given package name
    --root=<directory>
        path to the root directory of the image
"""
import os
import logging

# project
from kiwi.tasks.base import CliTask
from kiwi.privileges import Privileges
from kiwi.help import Help
from kiwi.system.prepare import SystemPrepare

log = logging.getLogger('kiwi')


class SystemUpdateTask(CliTask):
    """
    Implements update and maintenance of root systems

    Attributes

    * :attr:`manual`
        Instance of Help
    """
    def process(self):
        """
        Update root system with latest repository updates
        and optionally allow to add or delete packages. the options
        to add or delete packages can be used multiple times
        """
        self.manual = Help()
        if self._help():
            return

        Privileges.check_for_root_permissions()

        abs_root_path = os.path.abspath(self.command_args['--root'])

        self.load_xml_description(
            abs_root_path
        )

        package_requests = False
        if self.command_args['--add-package']:
            package_requests = True
        if self.command_args['--delete-package']:
            package_requests = True

        log.info('Updating system')
        self.system = SystemPrepare(
            self.xml_state,
            abs_root_path,
            allow_existing=True
        )
        manager = self.system.setup_repositories()

        if not package_requests:
            self.system.update_system(manager)
        else:
            if self.command_args['--add-package']:
                self.system.install_packages(
                    manager, self.command_args['--add-package']
                )
            if self.command_args['--delete-package']:
                self.system.delete_packages(
                    manager, self.command_args['--delete-package']
                )

    def _help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::system::update')
        else:
            return False
        return self.manual
