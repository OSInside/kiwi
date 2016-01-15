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
import marshal
import os

# project
from logger import log

from exceptions import (
    KiwiResultError
)


class Result(object):
    """
        Collect image building results
    """
    def __init__(self):
        self.result_files = {}

    def add(self, key, value):
        self.result_files[key] = value

    def get_results(self):
        return self.result_files

    def print_results(self):
        if self.result_files:
            log.info('Result files:')
            for key, value in self.result_files.iteritems():
                if value:
                    log.info('--> %s: %s', key, value)

    def dump(self, filename):
        try:
            marshal.dump(self, filename)
        except Exception as e:
            raise KiwiResultError(
                'Failed to marshal dump results: %s' % format(e)
            )

    @classmethod
    def load(self, filename):
        if not os.path.exists(filename):
            raise KiwiResultError(
                'No result information %s found' % filename
            )
        try:
            return marshal.load(filename)
        except Exception as e:
            raise KiwiResultError(
                'Failed to marshal load results: %s' % format(e)
            )
