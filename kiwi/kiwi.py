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
import logger
from app import App
from exceptions import KiwiError


def main():
    """
        kiwi - main entry
    """
    logger.init()
    try:
        App()
    except KiwiError as e:
        # known exception, log information and exit
        logger.log.error('%s: %s', type(e).__name__, format(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.log.error('kiwi aborted by keyboard interrupt')
        sys.exit(1)
    except docopt.DocoptExit:
        # exception caught by docopt, results in usage message
        raise
    except SystemExit:
        # user exception, program aborted by user
        sys.exit(1)
    except Exception:
        # exception we did no expect, show python backtrace
        logger.log.error('Unexpected error:')
        raise
