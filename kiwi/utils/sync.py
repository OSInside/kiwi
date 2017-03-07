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
import xattr

# project
from kiwi.logger import log
from kiwi.command import Command


class DataSync(object):
    """
    Sync data from a source directory to a target directory
    using the rsync protocol

    Attributes

    * :attr:`source_dir`
        source directory path name

    * :attr:`target_dir`
        target directory path name
    """
    def __init__(self, source_dir, target_dir):
        self.source_dir = source_dir
        self.target_dir = target_dir

    def sync_data(self, options=None, exclude=None):
        """
        Sync data from source to target using rsync

        :param list options: rsync options
        :param list exclude: file patterns to exclude
        """
        exclude_options = []
        rsync_options = []
        if options:
            rsync_options = options
        if not self.target_supports_extended_attributes():
            warn_me = False
            if '-X' in rsync_options:
                rsync_options.remove('-X')
                warn_me = True
            if '-A' in rsync_options:
                rsync_options.remove('-A')
                warn_me = True
            if warn_me:
                log.warning(
                    'Extended attributes not supported for target: %s',
                    self.target_dir
                )
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

    def target_supports_extended_attributes(self):
        """
        Check if the target directory supports extended filesystem
        attributes

        :rtype: bool
        """
        try:
            xattr.getxattr(self.target_dir, 'user.mime_type')
        except Exception as e:
            if format(e).startswith('[Errno 95]'):
                # libc interface [Errno 95] Operation not supported:
                return False
        return True
