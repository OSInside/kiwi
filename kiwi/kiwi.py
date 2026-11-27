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
import signal
import logging
from types import FrameType
from typing import Optional

# project
from kiwi.app import App
from kiwi.exceptions import KiwiError

log = logging.getLogger('kiwi')


class KiwiTerminated(BaseException):
    """
    Raised if kiwi receives a termination signal, see terminate.
    Like KeyboardInterrupt it is not an Exception, such that it is
    not handled by code handling errors and ends the program

    :param int signum: number of the received signal
    """

    def __init__(self, signum: int) -> None:
        super().__init__(signal.Signals(signum).name)
        self.signum = signum


def terminate(signum: int, frame: Optional[FrameType]) -> None:
    """
    Signal handler for termination signals, e.g SIGTERM

    Python ends the program on these signals without unwinding the
    stack. The cleanup of kiwi, e.g of temporary files, mounts and
    devices, only happens while the stack unwinds. Thus the signal
    raises KiwiTerminated, as a keyboard interrupt does for SIGINT.
    Another signal of the same kind ends kiwi immediately, e.g if
    the cleanup does not finish

    :param int signum: number of the received signal
    :param FrameType frame: current stack frame
    """
    signal.signal(signum, signal.SIG_DFL)
    raise KiwiTerminated(signum)


def main() -> None:
    """
    kiwi - main application entry point

    Initializes a global log object and handles all errors of the
    application. Every known error is inherited from KiwiError,
    everything else is passed down until the generic Exception
    which is handled as unexpected error including the python
    backtrace
    """
    for signum in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, terminate)
    try:
        App()
    except KiwiError as e:
        # known exception, log information and exit
        log.error('%s: %s', type(e).__name__, format(e))
        sys.exit(1)
    except KeyboardInterrupt:
        log.error('kiwi aborted by keyboard interrupt')
        sys.exit(1)
    except KiwiTerminated as e:
        log.error('kiwi terminated by signal %s', format(e))
        # exit status of a program ended by the signal
        sys.exit(128 + e.signum)
    except SystemExit as e:
        # user exception, program aborted by user
        sys.exit(e.code)
    except Exception:
        # exception we did no expect, show python backtrace
        log.error('Unexpected error:')
        raise
