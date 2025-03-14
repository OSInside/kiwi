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
# TODO: check how plugins can work when docopt is gone
import typer
import logging
import sys
import os
from unittest.mock import patch
from importlib.metadata import entry_points
from pathlib import Path
from typing import (
    Annotated, Dict, Optional, List
)

# project
from kiwi.exceptions import (
    KiwiUnknownServiceName,
    KiwiCommandNotLoaded,
    KiwiLoadCommandUndefined
)
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
    global_args = {}
    subcommand_args = {}
    cli_ok = False

    # system
    system = typer.Typer()

    # result
    result = typer.Typer()

    # image
    image = typer.Typer()

    cli = typer.Typer()
    cli.add_typer(system, name='system')
    cli.add_typer(result, name='result')
    cli.add_typer(image, name='image')

    def __init__(self):
        with patch('sys.exit'):
            self.cli()

        # FIXME: this is only here during development
        # print(self.global_args)
        # print(self.subcommand_args)

        if not self.cli_ok:
            sys.exit(1)

        self.command_args = self.get_command_args(
            raise_if_no_command=False
        )
        self.command_loaded = None

        # FIXME: this is only here during development
        print("OK")
        # sys.exit(0)

    @staticmethod
    def version(perform: bool):
        if perform:
            print(f'KIWI (next generation) version {__version__}')
            raise typer.Exit()

    @cli.callback()
    def main(
        color_output: Annotated[
            bool, typer.Option(
                help='use colors for warning and error messages'
            )
        ] = False,
        config: Annotated[
            Optional[Path], typer.Option(
                help='use specified runtime configuration file. If '
                'not specified the runtime configuration is looked '
                'up at ~/.config/kiwi/config.yml or /etc/kiwi.yml'
            )
        ] = None,
        debug: Annotated[
            bool, typer.Option(
                '--debug',
                help='print debug information, same as: --loglevel 10'
            )
        ] = False,
        debug_run_scripts_in_screen: Annotated[
            bool, typer.Option(
                '--debug-run-scripts-in-screen',
                help='run scripts called by kiwi in a screen session'
            )
        ] = False,
        kiwi_file: Annotated[
            Optional[str], typer.Option(
                help='Basename of kiwi file which contains the main image '
                'configuration elements. If not specified kiwi searches '
                'for a file named config.xml or a file matching *.kiwi'
            )
        ] = '',
        logfile: Annotated[
            Optional[Path], typer.Option(
                help='create a log file containing all log information '
                'including debug information even if this was not requested '
                'by the debug switch. The special call: "--logfile stdout" '
                'sends all information to standard out instead of writing to '
                'a file'
            )
        ] = None,
        logsocket: Annotated[
            Optional[Path], typer.Option(
                help='send log data to the given Unix Domain socket in '
                'the same format as with --logfile'
            )
        ] = None,
        loglevel: Annotated[
            Optional[int], typer.Option(
                help='specify logging level as number. Details about the '
                'available log levels can be found at: '
                'https://docs.python.org/3/library/logging.html#logging-levels '
                'Setting a log level causes all message >= level to be '
                'displayed.'
            )
        ] = None,
        profile: Annotated[
            Optional[List[str]], typer.Option(
                help='profile name, multiple profiles can be selected '
                'by passing this option multiple times'
            )
        ] = None,
        shared_cache_dir: Annotated[
            Optional[Path], typer.Option(
                help='specify an alternative shared cache directory. '
                'The directory is shared via bind mount between the '
                'build host and image root system and contains '
                'information about package repositories and their '
                'cache and meta data.'
            )
        ] = None,
        target_arch: Annotated[
            Optional[str], typer.Option(
                help='set the image architecture. By default the host '
                'architecture is used as the image architecture. If the '
                'specified architecture name does not match the host '
                'architecture and is therefore requesting a cross '
                'architecture image build, it is important to understand '
                'that for this process to work a preparatory step to '
                'support the image architecture and binary format on the '
                'building host is required first.'
            )
        ] = '',
        temp_dir: Annotated[
            Optional[Path], typer.Option(
                help='specify an alternative base temporary directory. '
                'The provided path is used as base directory to store '
                'temporary files and directories.'
            )
        ] = '/var/tmp',
        type: Annotated[
            Optional[str], typer.Option(
                help='image build type. If not set the default XML '
                'specified build type will be used'
            )
        ] = '',
        version: Annotated[
            Optional[bool], typer.Option(
                '--version', help='show program version', callback=version
            )
        ] = None
    ) -> Dict:
        """
        KIWI - Appliance Builder
        """
        Cli.global_args['--color-output'] = color_output
        Cli.global_args['--config'] = config
        Cli.global_args['--debug'] = debug
        Cli.global_args['--debug-run-scripts-in-screen'] = \
            debug_run_scripts_in_screen
        Cli.global_args['--kiwi-file'] = kiwi_file
        Cli.global_args['--logfile'] = logfile
        Cli.global_args['--loglevel'] = loglevel
        Cli.global_args['--logsocket'] = logsocket
        Cli.global_args['--profile'] = profile
        Cli.global_args['--shared-cache-dir'] = shared_cache_dir
        Cli.global_args['--target-arch'] = target_arch
        Cli.global_args['--temp-dir'] = temp_dir
        Cli.global_args['--type'] = type
        Cli.global_args['command'] = None
        Cli.global_args['image'] = False
        Cli.global_args['result'] = False
        Cli.global_args['system'] = False

    @cli.command()
    def help(command: Annotated[str, typer.Argument()] = 'kiwi'):
        manual = Help()
        manual.show(command)

    @image.command()
    def info(
        description: Annotated[
            Path, typer.Option(
                help='the description must be a directory '
                'containing a kiwi XML description and '
                'optional metadata files'
            )
        ],
        resolve_package_list: Annotated[
            bool, typer.Option(
                help='solve package dependencies and return a '
                'list of all packages including their attributes '
                'e.g. size, shasum, etc...'
            )
        ] = False,
    ):
        # TODO
        Cli.subcommand_args['image_info'] = {
        }
        Cli.cli_ok = True

    @image.command()
    def resize():
        # TODO
        Cli.subcommand_args['image_resize'] = {
        }
        Cli.cli_ok = True

    @result.command()
    def list():
        # TODO
        Cli.subcommand_args['result_list'] = {
        }
        Cli.cli_ok = True

    @result.command()
    def bundle():
        # TODO
        Cli.subcommand_args['result_bundle'] = {
        }
        Cli.cli_ok = True

    @system.command()
    def build():
        # TODO
        Cli.subcommand_args['system_build'] = {
        }
        Cli.cli_ok = True

    @system.command()
    def prepare():
        # TODO
        Cli.subcommand_args['system_prepare'] = {
        }
        Cli.cli_ok = True

    @system.command()
    def update():
        # TODO
        Cli.subcommand_args['system_update'] = {
        }
        Cli.cli_ok = True

    @system.command()
    def create():
        # TODO
        Cli.subcommand_args['system_create'] = {
        }
        Cli.cli_ok = True

    def get_servicename(self):
        """
        Extract service name from argument parse result

        :return: service name

        :rtype: str
        """
        if self.global_args.get('image') is True:
            return 'image'
        elif self.global_args.get('system') is True:
            return 'system'
        elif self.global_args.get('result') is True:
            return 'result'
        else:
            raise KiwiUnknownServiceName(
                'Unknown/Invalid Servicename'
            )

    def get_command(self):
        """
        Extract selected command name

        :return: command name
        :rtype: str
        """
        return self.global_args['command']

    def get_command_args(self, raise_if_no_command: bool = True) -> Dict:
        """
        Get argument dict for selected command
        including global options

        :return:
            Contains dictionary of command arguments

            .. code:: python

                {
                    '--some-option-name': 'value'
                }

        :rtype: dict
        """
        result = self.global_args
        command = self.get_command()
        if self.subcommand_args.get(command):
            return result.update(
                self.subcommand_args.get(command)
            )
        elif raise_if_no_command:
            raise KiwiCommandNotLoaded(
                f'{command} command not loaded'
            )

    def get_global_args(self):
        """
        Get argument dict for global arguments

        :return:
            Contains dictionary of global arguments

            .. code:: python

                {
                    '--some-global-option': 'value'
                }

        :rtype: dict
        """
        result = {}
        for arg, value in list(self.global_args.items()):
            if not arg == 'command':
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
                if arg == '--config' and value:  # pragma: no cover
                    Defaults.set_custom_runtime_config_file(value)
                result[arg] = value
        return result

    def load_command(self):
        """
        Loads task class plugin according to service and command name

        :return: loaded task module

        :rtype: object
        """
        discovered_tasks = {}
        if sys.version_info >= (3, 12):
            for entry in list(entry_points()):  # pragma: no cover
                if entry.group == 'kiwi.tasks':
                    discovered_tasks[entry.name] = entry.load()
        else:  # pragma: no cover
            module_entries = dict.get(entry_points(), 'kiwi.tasks')
            for entry in module_entries:
                discovered_tasks[entry.name] = entry.load()

        service = self.get_servicename()
        command = self.get_command()

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
