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

# project
from logger import log


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
            log.info('Created following result files')
            for key, value in self.result_files.iteritems():
                if value:
                    log.info('--> %s: %s', key, value)

    def dump(self, filename):
        marshal.dump(self, filename)

    @classmethod
    def load(self, filename):
        return marshal.load(filename)
