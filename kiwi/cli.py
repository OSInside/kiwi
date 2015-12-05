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
usage: kiwi -h | --help
       kiwi [--profile=<name>...]
            [--type=<build_type>]
            [--logfile=<filename>]
            [--debug]
           system <command> [<args>...]
       kiwi -v | --version
       kiwi help

global options:
    -v --version
        show program version
    --profile=<name>
        profile name, multiple profiles can be selected by passing
        this option multiple times
    --type=<build_type>
        image build type. If not set the default XML specified
        build type will be used
    --logfile=<filename>
        create a log file containing all log information including
        debug information even if this is was not requested by the
        debug switch
    --debug
        print debug information
    help
        show manual page
"""
import sys
import importlib
from docopt import docopt

# project
from exceptions import (
    KiwiUnknownServiceName,
    KiwiCommandNotLoaded,
    KiwiLoadCommandUndefined,
    KiwiUnknownCommand
)
from version import __VERSION__
from help import Help


class Cli(object):
    """
        Commandline interface
    """
    def __init__(self):
        self.all_args = docopt(
            __doc__,
            version='kiwi version ' + __VERSION__,
            options_first=True
        )
        self.command_args = self.all_args['<args>']
        self.command_loaded = None

    def show_and_exit_on_help_request(self):
        if self.all_args['help']:
            manual = Help()
            manual.show('kiwi')
            sys.exit(0)

    def get_servicename(self):
        if self.all_args['system']:
            return 'system'
        else:
            raise KiwiUnknownServiceName(
                'Unknown/Invalid Servicename'
            )

    def get_command(self):
        return self.all_args['<command>']

    def get_command_args(self):
        return self.__load_command_args()

    def get_global_args(self):
        result = {}
        for arg, value in self.all_args.iteritems():
            if not arg == '<command>' and not arg == '<args>':
                result[arg] = value
        return result

    def load_command(self):
        command = self.get_command()
        service = self.get_servicename()
        if not command:
            raise KiwiLoadCommandUndefined(
                'No command specified for %s service' % service
            )
        try:
            self.command_loaded = importlib.import_module(
                'kiwi.' + service + '_' + command + '_task'
            )
        except Exception as e:
            raise KiwiUnknownCommand(
                'Loading command %s for %s service failed with: %s: %s' %
                (command, service, type(e).__name__, format(e))
            )
        return self.command_loaded

    def __load_command_args(self):
        try:
            argv = [
                self.get_servicename(), self.get_command()
            ] + self.command_args
            return docopt(self.command_loaded.__doc__, argv=argv)
        except Exception:
            raise KiwiCommandNotLoaded(
                '%s command not loaded' % self.get_command()
            )
