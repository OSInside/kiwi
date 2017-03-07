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
from tempfile import mkdtemp
from six.moves.urllib.parse import urlparse
import hashlib

# project
from kiwi.mount_manager import MountManager
from kiwi.path import Path

from kiwi.exceptions import (
    KiwiUriStyleUnknown,
    KiwiUriTypeUnknown
)


class Uri(object):
    """
    Normalize url types available in a kiwi configuration into
    standard mime types.

    Attributes

    * :attr:`repo_type`
        Repository type name

    * :attr:`uri`
        URI, repository location, file

    * :attr:`repo_type`
        repository type name, rpm-dir, rpm-md, yast2

    * :attr:`mount_stack`
        list of mounted locations

    * :attr:`remote_uri_types`
        dictionary of remote uri type names

    * :attr:`local_uri_type`
        dictionary of local uri type names
    """
    def __init__(self, uri, repo_type):
        self.repo_type = repo_type
        self.uri = uri
        self.repo_type = repo_type
        self.mount_stack = []

        self.remote_uri_types = {
            'http': True,
            'https': True,
            'ftp': True,
            'obs': True,
            'ibs': True
        }
        self.local_uri_type = {
            'iso': True,
            'dir': True,
            'file': True,
            'suse': True
        }

    def translate(self):
        """
        Translate repository location according to their URI type

        Depending on the URI type the provided location needs to
        be adapted e.g loop mounted in case of an ISO or updated
        by the service URL in case of an open buildservice project
        name
        """
        uri = urlparse(self.uri)
        if not uri.scheme:
            raise KiwiUriStyleUnknown(
                'URI scheme not detected {uri}'.format(uri=self.uri)
            )

        if uri.scheme == 'obs' and self.repo_type == 'yast2':
            return self._obs_distribution(
                ''.join([uri.netloc, uri.path])
            )
        elif uri.scheme == 'obs':
            return self._obs_project(
                ''.join([uri.netloc, uri.path])
            )
        elif uri.scheme == 'ibs':
            return self._ibs_project(
                ''.join([uri.netloc, uri.path])
            )
        elif uri.scheme == 'dir':
            return self._local_path(uri.path)
        elif uri.scheme == 'file':
            return self._local_path(uri.path)
        elif uri.scheme == 'iso':
            return self._iso_mount_path(uri.path)
        elif uri.scheme == 'suse':
            return self._suse_buildservice_path(
                ''.join([uri.netloc, uri.path])
            )
        elif uri.scheme == 'http' or uri.scheme == 'ftp':
            return ''.join([uri.scheme, '://', uri.netloc, uri.path])
        else:
            raise KiwiUriStyleUnknown(
                'URI schema %s not supported' % self.uri
            )

    def credentials_file_name(self):
        """
        Filename to store repository credentials
        """
        uri = urlparse(self.uri)
        # initialize query with default credentials file name.
        # The information will be overwritten if the uri contains
        # a parameter query with a credentials parameter
        query = {'credentials': 'kiwiRepoCredentials'}

        if uri.query:
            query = dict(params.split('=') for params in uri.query.split('&'))

        return query['credentials']

    def alias(self):
        """
        Create hexdigest from URI as alias

        If the repository definition from the XML description does
        not provide an alias, kiwi creates one for you. However it's
        better to assign a human readable alias in the XML
        configuration

        :return: alias name as hexdigest
        :rtype: string
        """
        return hashlib.md5(self.uri.encode()).hexdigest()

    def is_remote(self):
        """
        Check if URI is a remote or local location

        :rtype: bool
        """
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

    def _iso_mount_path(self, path):
        # The prefix name 'kiwi_iso_mount' has a meaning here because the
        # zypper repository manager looks up iso mount paths by its repo
        # source name
        iso_mount_path = mkdtemp(prefix='kiwi_iso_mount.')
        iso_mount = MountManager(
            device=path, mountpoint=iso_mount_path
        )
        self.mount_stack.append(iso_mount)
        iso_mount.mount()
        return iso_mount.mountpoint

    def _local_path(self, path):
        return os.path.normpath(path)

    def _obs_project(self, name):
        return ''.join(['http://download.opensuse.org/repositories/', name])

    def _ibs_project(self, name):
        ibs_project = 'http://download.suse.de/ibs/'
        return ibs_project + name.replace(':', ':/')

    def _obs_distribution(self, name):
        if name == 'openSUSE:Factory/standard':
            # special handling for SUSE factory repo
            obs_distribution = \
                'http://download.opensuse.org/tumbleweed/repo/oss'
        else:
            obs_distribution = ''.join(
                ['http://download.opensuse.org/distribution/', name]
            )
        return obs_distribution

    def _suse_buildservice_path(self, name):
        """
        Special to openSUSE buildservice. If the buildservice builds
        the image it arranges the repos for each build in a special
        environment, the so called build worker.
        """
        return self._local_path(
            '/usr/src/packages/SOURCES/repos/' + name
        )

    def __del__(self):
        for mount in reversed(self.mount_stack):
            if mount.is_mounted():
                if mount.umount():
                    Path.wipe(mount.mountpoint)
