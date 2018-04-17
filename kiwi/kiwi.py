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
import sys
import docopt

# project
from . import logger
from .app import App
from .exceptions import KiwiError
from .defaults import Defaults


def extras(help_, version, options, doc):
    """
    Overwritten method from docopt

    Shows our own usage message for -h|--help

    :param bool help_: indicate to show help
    :param string version: version string
    :param list options:
        list of option tuples

        .. code:: python

            [option(name='name', value='value')]
    :param string doc: docopt doc string
    """
    if help_ and any((o.name in ('-h', '--help')) and o.value for o in options):
        usage(doc.strip("\n"))
        sys.exit(1)
    if version and any(o.name == '--version' and o.value for o in options):
        print(version)
        sys.exit(0)


def main():
    """
    kiwi - main application entry point

    Initializes a global log object and handles all errors of the
    application. Every known error is inherited from KiwiError,
    everything else is passed down until the generic Exception
    which is handled as unexpected error including the python
    backtrace
    """
    docopt.__dict__['extras'] = extras
    try:
        App()
    except KiwiError as e:
        # known exception, log information and exit
        logger.log.error('%s: %s', type(e).__name__, format(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.log.error('kiwi aborted by keyboard interrupt')
        sys.exit(1)
    except docopt.DocoptExit as e:
        # exception thrown by docopt, results in usage message
        usage(e)
        sys.exit(1)
    except SystemExit as e:
        # user exception, program aborted by user
        sys.exit(e)
    except Exception:
        # exception we did no expect, show python backtrace
        logger.log.error('Unexpected error:')
        raise


def usage(command_usage):
    """
    Instead of the docopt way to show the usage information we
    provide a kiwi specific usage information. The usage
    data now always consists out of:

    1. the generic call
       kiwi [global options] service <command> [<args>]

    2. the command specific usage defined by the docopt string
       short form by default, long form with -h | --help

    3. the global options

    :param string command_usage: usage data
    """
    with open(Defaults.project_file('cli.py'), 'r') as cli:
        program_code = cli.readlines()

    global_options = '\n'
    process_lines = False
    for line in program_code:
        if line.rstrip().startswith('global options'):
            process_lines = True
        if line.rstrip() == '"""':
            process_lines = False
        if process_lines:
            global_options += format(line)

    print('usage: kiwi [global options] service <command> [<args>]\n')
    print(format(command_usage).replace('usage:', '      '))
    if 'global options' not in format(command_usage):
        print(format(global_options))
