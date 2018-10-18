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
import requests
import hashlib

# project
from kiwi.mount_manager import MountManager
from kiwi.path import Path
from kiwi.defaults import Defaults
from kiwi.runtime_config import RuntimeConfig
from kiwi.logger import log

from kiwi.exceptions import (
    KiwiUriStyleUnknown,
    KiwiUriTypeUnknown,
    KiwiUriOpenError
)


class Uri(object):
    """
    **Normalize url types available in a kiwi configuration into
    standard mime types**

    :param str repo_type: repository type name. Only needed if the uri
        is not enough to determine the repository type
        e.g for yast2 vs. rpm-md obs repositories
    :param str uri: URI, repository location, file
    :param list mount_stack: list of mounted locations
    :param dict remote_uri_types: dictionary of remote uri type names
    :param dict local_uri_type: dictionary of local uri type names
    """
    def __init__(self, uri, repo_type=None):
        self.runtime_config = RuntimeConfig()
        self.repo_type = repo_type
        self.uri = uri if not uri.startswith(os.sep) else ''.join(
            [Defaults.get_default_uri_type(), uri]
        )
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
            'file': True,
            'obsrepositories': True
        }

    def translate(self, check_build_environment=True):
        """
        Translate repository location according to their URI type

        Depending on the URI type the provided location needs to
        be adapted e.g loop mounted in case of an ISO or updated
        by the service URL in case of an open buildservice project
        name

        :raises KiwiUriStyleUnknown: if the uri scheme can't be detected, is
            unknown or it is inconsistent with the build environment
        :param bool check_build_environment: specify if the uri translation
            should depend on the environment the build is called in. As of
            today this only effects the translation result if the image
            build happens inside of the Open Build Service

        :rtype: str
        """
        uri = urlparse(self.uri)
        if not uri.scheme:
            raise KiwiUriStyleUnknown(
                'URI scheme not detected {uri}'.format(uri=self.uri)
            )
        elif uri.scheme == 'obs':
            if check_build_environment and Defaults.is_buildservice_worker():
                return self._buildservice_path(
                    name=''.join([uri.netloc, uri.path]).replace(':/', ':'),
                    fragment=uri.fragment,
                    urischeme=uri.scheme
                )
            else:
                return self._obs_project_download_link(
                    ''.join([uri.netloc, uri.path]).replace(':/', ':')
                )
        elif uri.scheme == 'obsrepositories':
            if not Defaults.is_buildservice_worker():
                raise KiwiUriStyleUnknown(
                    'Only the buildservice can use the {0} schema'.format(
                        uri.scheme
                    )
                )
            return self._buildservice_path(
                name=''.join([uri.netloc, uri.path]).replace(':/', ':'),
                fragment=uri.fragment,
                urischeme=uri.scheme
            )
        elif uri.scheme == 'dir':
            return self._local_path(uri.path)
        elif uri.scheme == 'file':
            return self._local_path(uri.path)
        elif uri.scheme == 'iso':
            return self._iso_mount_path(uri.path)
        elif uri.scheme.startswith('http') or uri.scheme == 'ftp':
            if self._get_credentials_uri() or not uri.query:
                return ''.join(
                    [uri.scheme, '://', uri.netloc, uri.path]
                )
            else:
                return ''.join(
                    [uri.scheme, '://', uri.netloc, uri.path, '?', uri.query]
                )
        else:
            raise KiwiUriStyleUnknown(
                'URI schema %s not supported' % self.uri
            )

    def credentials_file_name(self):
        """
        Filename to store repository credentials

        :return: credentials file name

        :rtype: str
        """
        uri = self._get_credentials_uri()
        # initialize query with default credentials file name.
        # The information will be overwritten if the uri contains
        # a parameter query with a credentials parameter
        query = {'credentials': 'kiwiRepoCredentials'}

        if uri:
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

        :rtype: str
        """
        return hashlib.md5(self.uri.encode()).hexdigest()

    def is_remote(self):
        """
        Check if URI is a remote or local location

        :return: True or False

        :rtype: bool
        """
        uri = urlparse(self.uri)
        if not uri.scheme:
            raise KiwiUriStyleUnknown(
                'URI scheme not detected %s' % self.uri
            )
        if uri.scheme == 'obs' and Defaults.is_buildservice_worker():
            return False
        elif uri.scheme in self.remote_uri_types:
            return True
        elif uri.scheme in self.local_uri_type:
            return False
        else:
            raise KiwiUriTypeUnknown(
                'URI type %s unknown' % uri.scheme
            )

    def is_public(self):
        """
        Check if URI is considered to be publicly reachable

        :return: True or False

        :rtype: bool
        """
        uri = urlparse(self.uri)
        if not uri.scheme:
            # unknown uri schema is considered not public
            return False
        elif uri.scheme == 'obs':
            # obs is public but only if the configured download_server is public
            return self.runtime_config.is_obs_public()
        elif uri.scheme in self.remote_uri_types:
            # listed in remote uri types, thus public
            return True
        else:
            # unknown uri type considered not public
            return False

    def get_fragment(self):
        """
        Returns the fragment part of the URI.

        :return: fragment part of the URI if any, None otherwise

        :rtype: str, None
        """
        uri = urlparse(self.uri)
        return uri.fragment

    def _get_credentials_uri(self):
        uri = urlparse(self.uri)
        if uri.query and uri.query.startswith('credentials='):
            return uri

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

    def _obs_project_download_link(self, name):
        name_parts = name.split(os.sep)
        repository = name_parts.pop()
        project = os.sep.join(name_parts)
        try:
            download_link = os.sep.join(
                [
                    self.runtime_config.get_obs_download_server_url(),
                    project.replace(':', ':/'), repository
                ]
            )
            if not Defaults.is_buildservice_worker():
                request = requests.get(download_link)
                request.raise_for_status()
                return request.url
            else:
                log.warning(
                    'Using {0} without location verification due to build '
                    'in isolated environment'.format(download_link)
                )
                return download_link
        except Exception as e:
            raise KiwiUriOpenError(
                '{0}: {1}'.format(type(e).__name__, format(e))
            )

    def _buildservice_path(self, name, urischeme, fragment=None):
        """
        Special to openSUSE buildservice. If the buildservice builds
        the image it arranges the repos for each build in a special
        environment, the so called build worker.
        """
        bs_source_dir = '/usr/src/packages/SOURCES'
        if self.repo_type == 'container':
            if urischeme == 'obsrepositories':
                local_path = os.sep.join(
                    [bs_source_dir, 'containers/_obsrepositories', name]
                )
            else:
                local_path = os.sep.join(
                    [bs_source_dir, 'containers', name]
                )
            if fragment:
                local_path = ''.join([local_path, '#', fragment])
        else:
            local_path = os.sep.join(
                [bs_source_dir, 'repos', name]
            )
        return self._local_path(local_path)

    def __del__(self):
        for mount in reversed(self.mount_stack):
            if mount.is_mounted():
                if mount.umount():
                    Path.wipe(mount.mountpoint)
