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
# project
from ..command import Command


class DataSync(object):
    """
        sync data from a source directory to a target directory
        using the rsync protocol
    """
    def __init__(self, source_dir, target_dir):
        self.source_dir = source_dir
        self.target_dir = target_dir

    def sync_data(self, options=None, exclude=None):
        exclude_options = []
        rsync_options = []
        if options:
            rsync_options = options
        if exclude:
            for item in exclude:
                exclude_options.append('--exclude')
                exclude_options.append(
                    '/' + item
                )
        Command.run(
            ['rsync'] + rsync_options + exclude_options + [
                self.source_dir, self.target_dir
            ]
        )
