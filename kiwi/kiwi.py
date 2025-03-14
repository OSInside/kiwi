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
import logging

# project
from kiwi.app import App
from kiwi.exceptions import KiwiError

log = logging.getLogger('kiwi')


def main():
    """
    kiwi - main application entry point

    Initializes a global log object and handles all errors of the
    application. Every known error is inherited from KiwiError,
    everything else is passed down until the generic Exception
    which is handled as unexpected error including the python
    backtrace
    """
    try:
        App()
    except KiwiError as e:
        # known exception, log information and exit
        log.error('%s: %s', type(e).__name__, format(e))
        sys.exit(1)
    except KeyboardInterrupt:
        log.error('kiwi aborted by keyboard interrupt')
        sys.exit(1)
    except SystemExit as e:
        # user exception, program aborted by user
        sys.exit(e)
    except Exception:
        # exception we did no expect, show python backtrace
        log.error('Unexpected error:')
        raise
