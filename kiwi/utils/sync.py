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
import os
import logging
from stat import ST_MODE
import xattr

# project
from kiwi.command import Command

log = logging.getLogger('kiwi')


class DataSync:
    """
    **Sync data from a source directory to a target directory
    using the rsync protocol**

    :param str source_dir: source directory path name
    :param str target_dir: target directory path name
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
        target_entry_permissions = None
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
        if os.path.exists(self.target_dir):
            target_entry_permissions = os.stat(self.target_dir)[ST_MODE]
        Command.run(
            ['rsync'] + rsync_options + exclude_options + [
                self.source_dir, self.target_dir
            ]
        )
        if target_entry_permissions:
            # rsync applies the permissions of the source directory
            # also to the target directory which is unwanted because
            # only permissions of the files and directories from the
            # source directory and its contents should be transfered
            # but not from the source directory itself. Therefore
            # the permission bits of the target directory before the
            # sync are applied back after sync to ensure they have
            # not changed
            os.chmod(self.target_dir, target_entry_permissions)

    def target_supports_extended_attributes(self):
        """
        Check if the target directory supports extended filesystem
        attributes

        :return: True or False

        :rtype: bool
        """
        try:
            xattr.getxattr(self.target_dir, 'user.mime_type')
        except Exception as e:
            if format(e).startswith('[Errno 95]'):
                # libc interface [Errno 95] Operation not supported:
                return False
        return True
