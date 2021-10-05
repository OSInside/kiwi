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
usage: kiwi-ng -h | --help
       kiwi-ng [--profile=<name>...]
               [--temp-dir=<directory>]
               [--type=<build_type>]
               [--logfile=<filename>]
               [--debug]
               [--color-output]
               [--config=<configfile>]
           image <command> [<args>...]
       kiwi-ng [--logfile=<filename>]
               [--debug]
               [--color-output]
               [--config=<configfile>]
           result <command> [<args>...]
       kiwi-ng [--profile=<name>...]
               [--shared-cache-dir=<directory>]
               [--temp-dir=<directory>]
               [--target-arch=<name>]
               [--type=<build_type>]
               [--logfile=<filename>]
               [--debug]
               [--color-output]
               [--config=<configfile>]
           system <command> [<args>...]
       kiwi-ng compat <legacy_args>...
       kiwi-ng --compat <legacy_args>...
       kiwi-ng -v | --version
       kiwi-ng help

global options:
    --color-output
        use colors for warning and error messages
    --config=<configfile>
        use specified runtime configuration file. If
        not specified the runtime configuration is looked
        up at ~/.config/kiwi/config.yml or /etc/kiwi.yml
    --logfile=<filename>
        create a log file containing all log information including
        debug information even if this is was not requested by the
        debug switch. The special call: '--logfile stdout' sends all
        information to standard out instead of writing to a file
    --debug
        print debug information
    -v --version
        show program version
    help
        show manual page

global options for services: image, system
    --profile=<name>
        profile name, multiple profiles can be selected by passing
        this option multiple times
    --shared-cache-dir=<directory>
        specify an alternative shared cache directory. The directory
        is shared via bind mount between the build host and image
        root system and contains information about package repositories
        and their cache and meta data.
    --temp-dir=<directory>
        specify an alternative base temporary directory. The
        provided path is used as base directory to store temporary
        files and directories. By default /var/tmp is used.
    --type=<build_type>
        image build type. If not set the default XML specified
        build type will be used

global options for services: system
    --target-arch=<name>
        set the image architecture. By default the host architecture is
        used as the image architecture. If the specified architecture name
        does not match the host architecture and is therefore requesting
        a cross architecture image build, it's important to understand that
        for this process to work a preparatory step to support the image
        architecture and binary format on the building host is required
        and not a responsibility of kiwi.
"""
import logging
import sys
import os
import pkg_resources
from docopt import docopt

# project
from kiwi.exceptions import (
    KiwiUnknownServiceName,
    KiwiCommandNotLoaded,
    KiwiLoadCommandUndefined,
    KiwiCompatError
)
from kiwi.path import Path
from kiwi.version import __version__
from kiwi.help import Help
from kiwi.defaults import Defaults

log = logging.getLogger('kiwi')


class Cli:
    """
    **Implements the main command line interface**

    An instance of the Cli class builds the entry point for the
    application and implements methods to load further command plugins
    which itself provides their own command line interface
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

        :rtype: str
        """
        if self.all_args.get('image') is True:
            return 'image'
        elif self.all_args.get('system') is True:
            return 'system'
        elif self.all_args.get('result') is True:
            return 'result'
        elif self.all_args.get('--compat') is True:
            return 'compat'
        elif self.all_args.get('compat') is True:
            return 'compat'
        else:
            raise KiwiUnknownServiceName(
                'Unknown/Invalid Servicename'
            )

    def invoke_kiwicompat(self, compat_args):
        """
        Execute kiwicompat with provided legacy KIWI command line arguments

        Example:

        .. code:: python

            invoke_kiwicompat(
                '--build', 'description', '--type', 'vmx',
                '-d', 'destination'
            )

        :param list compat_args: legacy kiwi command arguments
        """
        kiwicompat = Path.which('kiwicompat', access_mode=os.X_OK)
        try:
            os.execvp(kiwicompat, ['kiwicompat'] + compat_args)
        except Exception as e:
            raise KiwiCompatError(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def get_command(self):
        """
        Extract selected command name

        :return: command name
        :rtype: str
        """
        return self.all_args['<command>']

    def get_command_args(self):
        """
        Extract argument dict for selected command

        :return:
            Contains dictionary of command arguments

            .. code:: python

                {
                    '--command-option': 'value'
                }

        :rtype: dict
        """
        return self._load_command_args()

    def get_global_args(self):
        """
        Extract argument dict for global arguments

        :return:
            Contains dictionary of global arguments

            .. code:: python

                {
                    '--global-option': 'value'
                }

        :rtype: dict
        """
        result = {}
        for arg, value in list(self.all_args.items()):
            if not arg == '<command>' and not arg == '<args>':
                if arg == '--type' and value == 'vmx':
                    log.warning(
                        'vmx type is now a subset of oem, --type set to oem'
                    )
                    value = 'oem'
                if arg == '--shared-cache-dir' and not value:
                    value = os.sep + Defaults.get_shared_cache_location()
                if arg == '--shared-cache-dir' and value:
                    Defaults.set_shared_cache_location(value)
                if arg == '--temp-dir' and not value:
                    value = Defaults.get_temp_location()
                if arg == '--temp-dir' and value:
                    Defaults.set_temp_location(value)
                if arg == '--target-arch' and value:
                    Defaults.set_platform_name(value)
                if arg == '--config' and value:
                    Defaults.set_custom_runtime_config_file(value)
                result[arg] = value
        return result

    def load_command(self):
        """
        Loads task class plugin according to service and command name

        :return: loaded task module

        :rtype: object
        """
        discovered_tasks = {
            entry_point.name: entry_point.load()
            for entry_point in pkg_resources.iter_entry_points('kiwi.tasks')
        }
        service = self.get_servicename()
        command = self.get_command()

        if service == 'compat':
            compat_arguments = self.all_args['<legacy_args>']
            if '--' in compat_arguments:
                compat_arguments.remove('--')
            return self.invoke_kiwicompat(compat_arguments)

        if not command:
            raise KiwiLoadCommandUndefined(
                'No command specified for {0} service'.format(service)
            )

        self.command_loaded = discovered_tasks.get(
            service + '_' + command
        )
        if not self.command_loaded:
            prefix = 'usage:'
            discovered_tasks_for_service = ''
            for task in discovered_tasks:
                if task.startswith(service):
                    discovered_tasks_for_service += '{0} kiwi-ng {1}\n'.format(
                        prefix, task.replace('_', ' ')
                    )
                    prefix = '      '
            raise KiwiCommandNotLoaded(
                'Command "{0}" not found\n\n{1}'.format(
                    command, discovered_tasks_for_service
                )
            )
        return self.command_loaded

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
