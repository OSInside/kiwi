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
import re
import logging
from lxml import etree
from urllib.parse import (
    urlparse, ParseResult, quote
)
from urllib.request import urlopen
from urllib.request import Request
import requests
from uuid import uuid4
from typing import Optional

# project
from kiwi.defaults import Defaults
from kiwi.runtime_config import RuntimeConfig

from kiwi.exceptions import (
    KiwiUriStyleUnknown,
    KiwiUriTypeUnknown,
    KiwiUriOpenError
)

log = logging.getLogger('kiwi')


class Uri:
    """
    **Normalize and manage URI types**
    """
    def __init__(
        self, uri: str, repo_type: str = 'rpm-md', source_type: str = ''
    ):
        """
        Manage kiwi source URIs and allow transformation into
        standard URLs

        :param str uri: URI, remote, local or metalink repository location
            The resource type as part of the URI can be set to one of:
            * http:
            * https:
            * ftp:
            * obs:
            * dir:
            * file:
            * obsrepositories:
            * this:
            The special this:// type resolve to the image description
            directory. The code to resolve this is not part of the Uri
            class because it has no state information about the image
            description directory. Therefore the resolving of the this://
            path happens on construction of an XMLState object as
            part of the resolve_this_path() method. The method resolves
            the path into a native dir:// URI which can be properly
            handled here.
        :param str repo_type:
            repository type name, defaults to 'rpm-md' and is only
            effectively used when building inside of the open
            build service which maps local repositories to a
            specific environment
        :param str source_type:
            specify source type if the provided URI is a service.
            Currently only the metalink source type is handled
        """
        self.runtime_config = RuntimeConfig()

        if source_type == 'metalink':
            uri = self._resolve_metalink_uri(uri)

        self.repo_type = repo_type
        self.uri = uri if not uri.startswith(os.sep) else ''.join(
            [Defaults.get_default_uri_type(), uri]
        )

        self.remote_uri_types = {
            'http': True,
            'https': True,
            'ftp': True,
            'obs': True
        }
        self.local_uri_type = {
            'dir': True,
            'file': True,
            'obsrepositories': True
        }

    def translate(self, check_build_environment: bool = True) -> str:
        """
        Translate repository location according to their URI type

        Depending on the URI type the provided location needs to
        be adapted e.g updated by the service URL in case of an
        open buildservice project name

        :raises KiwiUriStyleUnknown: if the uri scheme can't be detected, is
            unknown or it is inconsistent with the build environment
        :param bool check_build_environment: specify if the uri translation
            should depend on the environment the build is called in. As of
            today this only effects the translation result if the image
            build happens inside of the Open Build Service

        :return: translated repository location

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
        elif uri.scheme.startswith('http') or uri.scheme == 'ftp':
            netloc = uri.netloc
            uri_with_credentials_pattern = '^(.*):(.*)@(.*)$'
            sensitive_match = re.match(uri_with_credentials_pattern, netloc)
            if sensitive_match:
                netloc = "{0}:{1}@{2}".format(
                    quote(sensitive_match.group(1)),
                    quote(sensitive_match.group(2)),
                    sensitive_match.group(3)
                )
            if self._get_credentials_uri() or not uri.query:
                return ''.join(
                    [uri.scheme, '://', netloc, uri.path]
                )
            else:
                return ''.join(
                    [uri.scheme, '://', netloc, uri.path, '?', uri.query]
                )
        else:
            raise KiwiUriStyleUnknown(
                'URI schema %s not supported' % self.uri
            )

    @staticmethod
    def print_sensitive(location: str) -> str:
        uri_with_credentials_pattern = '^.*://(.*:.*)@.*'
        sensitive_match = re.match(uri_with_credentials_pattern, location)
        if sensitive_match:
            return location.replace(sensitive_match.group(1), '******')
        else:
            return location

    def credentials_file_name(self) -> str:
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
            query = dict(params.split('=') for params in uri.query.split('&'))  # type: ignore

        return query['credentials']

    def alias(self) -> str:
        """
        Create hex representation of uuid4

        If the repository definition from the XML description does
        not provide an alias, kiwi creates one for you. However it's
        better to assign a human readable alias in the XML
        configuration

        :return: alias name as hex representation of uuid4

        :rtype: str
        """
        return uuid4().hex

    def is_remote(self) -> bool:
        """
        Check if URI is a remote or local location

        :return: True|False

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

    def is_public(self) -> bool:
        """
        Check if URI is considered to be publicly reachable

        :return: True|False

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

    def get_fragment(self) -> str:
        """
        Returns the fragment part of the URI.

        :return: fragment part of the URI if any, empty string otherwise

        :rtype: str
        """
        uri = urlparse(self.uri)
        return uri.fragment

    def _get_credentials_uri(self) -> Optional[ParseResult]:
        uri = urlparse(self.uri)
        credentials_uri = None
        if uri.query and uri.query.startswith('credentials='):
            credentials_uri = uri
        return credentials_uri

    def _local_path(self, path: str) -> str:
        return os.path.abspath(os.path.normpath(path))

    def _obs_project_download_link(self, name: str) -> str:
        name_parts = name.split(os.sep)
        repository = name_parts.pop()
        project = os.sep.join(name_parts)
        download_link = None
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
        except Exception as issue:
            raise KiwiUriOpenError(
                f'{download_link}: {issue}'
            )

    def _buildservice_path(
        self, name: str, urischeme: str, fragment: str = ''
    ) -> str:
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

    def _resolve_metalink_uri(self, uri: str) -> str:
        selected_repo_source = uri
        namespace_map = dict(
            metalink="http://www.metalinker.org/"
        )
        expression = '//metalink:file[@name="repomd.xml"]/metalink:resources/*'
        try:
            metalink_location = urlopen(Request(uri))
            xml = etree.parse(metalink_location)
            url_list = xml.getroot().xpath(
                expression, namespaces=namespace_map
            )
            source_dict = {}
            for url in url_list:
                if url.get('protocol') == 'https':
                    source_dict[url.text] = int(url.get('preference'))
            start_preference = 0
            for url in sorted(source_dict.keys()):
                preference = source_dict[url]
                if preference > start_preference:
                    selected_repo_source = url
                    start_preference = preference
        except Exception as issue:
            raise KiwiUriOpenError(
                f'Failed to resolve metalink URI: {issue}'
            )
        selected_repo_source = selected_repo_source.replace(
            'repodata/repomd.xml', ''
        )
        return selected_repo_source
