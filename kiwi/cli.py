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
            [--color-output]
           image <command> [<args>...]
       kiwi [--debug]
            [--color-output]
           result <command> [<args>...]
       kiwi [--profile=<name>...]
            [--type=<build_type>]
            [--logfile=<filename>]
            [--debug]
            [--color-output]
           system <command> [<args>...]
       kiwi --compat <legacy_args>...
       kiwi -v | --version
       kiwi help

global options:
    --color-output
        use colors for warning and error messages
    --compat
        support legacy kiwi commandline, e.g
        kiwi --compat -- --build /my/description --type vmx -d /my/dest
    --debug
        print debug information
    -v --version
        show program version
    help
        show manual page

global options for services: image, system
    --logfile=<filename>
        create a log file containing all log information including
        debug information even if this is was not requested by the
        debug switch
    --profile=<name>
        profile name, multiple profiles can be selected by passing
        this option multiple times
    --type=<build_type>
        image build type. If not set the default XML specified
        build type will be used
"""
from __future__ import print_function
import sys
import glob
import re
import os
import importlib
from docopt import docopt

# project
from .exceptions import (
    KiwiUnknownServiceName,
    KiwiCommandNotLoaded,
    KiwiLoadCommandUndefined,
    KiwiCompatError
)
from .defaults import Defaults
from .version import __version__
from .help import Help


class Cli(object):
    """
    Implements the main command line interface

    An instance of the Cli class builds the entry point for the
    application and implements methods to load further command plugins
    which itself provides their own command line interface

    Attributes

    * :attr:`all_args`
        docopt parse result, all arguments dict

    * :attr:`command_args`
        subset of docopt argument dict for selected command

    * :attr:`command_loaded`
        result of importlib command load operation
    """
    def __init__(self):
        self.all_args = docopt(
            __doc__,
            version='KIWI (next generation) version ' + __version__,
            options_first=True
        )
        self.command_args = self.all_args['<args>']
        self.command_loaded = None

    def show_and_exit_on_help_request(self):
        """
        Execute man to show the selected manual page
        """
        if self.all_args['help']:
            manual = Help()
            manual.show('kiwi')
            sys.exit(0)

    def get_servicename(self):
        """
        Extract service name from argument parse result

        :return: service name
        :rtype: string
        """
        if self.all_args.get('image') is True:
            return 'image'
        elif self.all_args.get('system') is True:
            return 'system'
        elif self.all_args.get('result') is True:
            return 'result'
        elif self.all_args.get('--compat') is True:
            return 'compat'
        else:
            raise KiwiUnknownServiceName(
                'Unknown/Invalid Servicename'
            )

    def invoke_kiwicompat(self, compat_args):
        """
        Execute kiwicompat with provided command line arguments

        :param list compat_args: raw arguments
        """
        try:
            os.execvp('kiwicompat', ['kiwicompat'] + compat_args)
        except Exception as e:
            raise KiwiCompatError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def get_command(self):
        """
        Extract selected command name

        :return: command name
        :rtype: string
        """
        return self.all_args['<command>']

    def get_command_args(self):
        """
        Extract argument dict for selected command

        :return: command arguments
        :rtype: dict
        """
        return self._load_command_args()

    def get_global_args(self):
        """
        Extract argument dict for global arguments

        :return: global arguments
        :rtype: dict
        """
        result = {}
        for arg, value in list(self.all_args.items()):
            if not arg == '<command>' and not arg == '<args>':
                result[arg] = value
        return result

    def load_command(self):
        """
        Loads task class plugin according to service and command name
        """
        command = self.get_command()
        service = self.get_servicename()
        if service == 'compat':
            return self.invoke_kiwicompat(
                self.all_args['<legacy_args>'][1:]
            )
        if not command:
            raise KiwiLoadCommandUndefined(
                'No command specified for %s service' % service
            )
        command_source_file = Defaults.project_file(
            'tasks/' + service + '_' + command + '.py'
        )
        if not os.path.exists(command_source_file):
            prefix = 'usage:'
            for service_command in self._get_command_implementations(service):
                print('%s kiwi %s' % (prefix, service_command))
                prefix = '      '
            raise SystemExit(1)
        self.command_loaded = importlib.import_module(
            'kiwi.tasks.' + service + '_' + command
        )
        return self.command_loaded

    def _get_command_implementations(self, service):
        command_implementations = []
        glob_match = Defaults.project_file('/') + 'tasks/*.py'
        for source_file in glob.iglob(glob_match):
            with open(source_file, 'r') as source:
                for line in source:
                    if re.search('usage: (.*)', line):
                        command_path = os.path.basename(
                            source_file
                        ).replace('.py', '').split('_')
                        if command_path[0] == service:
                            command_implementations.append(
                                ' '.join(command_path)
                            )
                        break
        return command_implementations

    def _load_command_args(self):
        try:
            argv = [
                self.get_servicename(), self.get_command()
            ] + self.command_args
            return docopt(self.command_loaded.__doc__, argv=argv)
        except Exception:
            raise KiwiCommandNotLoaded(
                '%s command not loaded' % self.get_command()
            )
