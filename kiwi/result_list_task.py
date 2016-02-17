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
usage: kiwi result list -h | --help
       kiwi result list --target-dir=<directory>
       kiwi result list help

commands:
    list
        list result information from a previous system command

options:
    --target-dir=<directory>
        the target directory as it was used in a system command
"""
import os

# project
from .cli_task import CliTask
from .help import Help
from .result import Result
from .logger import log


class ResultListTask(CliTask):
    """
        Implements result listing
    """
    def process(self):
        self.manual = Help()
        if self.__help():
            return

        result_directory = os.path.normpath(
            self.command_args['--target-dir']
        )
        log.info(
            'Listing results from %s', result_directory
        )
        result = Result.load(
            result_directory + '/kiwi.result'
        )
        result.print_results()

    def __help(self):
        if self.command_args['help']:
            self.manual.show('kiwi::result::list')
        else:
            return False
        return self.manual
