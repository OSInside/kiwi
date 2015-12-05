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
from tempfile import mkdtemp
from urlparse import urlparse
import hashlib

# project
from command import Command
from path import Path

from exceptions import (
    KiwiUriStyleUnknown,
    KiwiUriTypeUnknown
)


class Uri(object):
    """
        normalize url types available in a kiwi configuration into
        standard mime types.
    """
    def __init__(self, uri, repo_type):
        self.repo_type = repo_type
        self.uri = uri
        self.mount_stack = []

        self.remote_uri_types = {
            'http': True,
            'https': True,
            'ftp': True,
            'obs': True
        }
        self.local_uri_type = {
            'iso': True,
            'dir': True,
            'this': True
        }

    def translate(self):
        uri = urlparse(self.uri)
        if not uri.scheme:
            raise KiwiUriStyleUnknown(
                'URI scheme not detected %s' % self.uri
            )

        if uri.scheme == 'obs' and self.repo_type == 'yast2':
            return self.__obs_distribution(
                uri.netloc + uri.path
            )
        elif uri.scheme == 'obs':
            return self.__obs_project(
                uri.netloc + uri.path
            )
        elif uri.scheme == 'dir':
            return self.__local_directory(uri.path)
        elif uri.scheme == 'iso':
            return self.__iso_mount_path(uri.path)
        elif uri.scheme == 'http':
            return self.uri
        else:
            raise KiwiUriStyleUnknown(
                'URI schema %s not supported' % self.uri
            )

    def alias(self):
        return hashlib.md5(self.uri).hexdigest()

    def is_remote(self):
        uri = urlparse(self.uri)
        if not uri.scheme:
            raise KiwiUriStyleUnknown(
                'URI scheme not detected %s' % self.uri
            )
        if uri.scheme in self.remote_uri_types:
            return True
        else:
            if uri.scheme in self.local_uri_type:
                return False
            else:
                raise KiwiUriTypeUnknown(
                    'URI type %s unknown' % uri.scheme
                )

    def __iso_mount_path(self, path):
        iso_path = mkdtemp()
        Command.run(['mount', path, iso_path])
        self.mount_stack.append(iso_path)
        return iso_path

    def __local_directory(self, path):
        return path

    def __obs_project(self, name):
        obs_project = 'http://download.opensuse.org/repositories/'
        return obs_project + name

    def __obs_distribution(self, name):
        obs_distribution = 'http://download.opensuse.org/distribution/'
        return obs_distribution + name

    def __del__(self):
        try:
            for mount in reversed(self.mount_stack):
                Command.run(['umount', mount])
                Path.remove(mount)
        except Exception:
            pass
