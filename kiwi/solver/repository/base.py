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
from base64 import b64encode
from urllib.request import urlopen
from urllib.request import Request
from tempfile import NamedTemporaryFile
from tempfile import mkdtemp
from lxml import etree
import random
import glob
import os

# project
from kiwi.exceptions import KiwiUriOpenError
from kiwi.path import Path
from kiwi.command import Command
from kiwi.defaults import Defaults


class SolverRepositoryBase:
    """
    **Base class interface for SAT solvable creation.**

    :param object uri: Instance of :class:`Uri`
    :param string user: User name for uri authentication
    :param string secret: Secret token for uri authentication
    """
    def __init__(self, uri, user=None, secret=None):
        self.uri = uri
        self.user = user
        self.secret = secret
        self._init_temporary_dir_names()

    def create_repository_solvable(
        self, target_dir=Defaults.get_solvable_location()
    ):
        """
        Create SAT solvable for this repository from previously
        created intermediate solvables by merge and store the
        result solvable in the specified target_dir

        :param str target_dir: path name

        :return: file path to solvable

        :rtype: str
        """
        Path.create(target_dir)
        solvable = os.sep.join(
            [target_dir, self.uri.alias()]
        )
        if not self.is_uptodate(target_dir):
            self._setup_repository_metadata()
            solvable = self._merge_solvables(target_dir)
            self._cleanup()

        return solvable

    def timestamp(self):
        """
        Return repository timestamp

        The retrieval of the repository timestamp depends on the
        type of the repository and is therefore supposed to be implemented
        in the specialized Solver Repository classes. If no such
        implementation exists the method returns the value 'static'
        to indicate there is no timestamp information available.

        :rtype: str
        """
        return 'static'

    def is_uptodate(self, target_dir=Defaults.get_solvable_location()):
        """
        Check if repository metadata is up to date

        :return: True or False

        :rtype: bool
        """
        solvable_time_file = ''.join(
            [target_dir, os.sep, self.uri.alias(), '.timestamp']
        )
        if os.path.exists(solvable_time_file):
            with open(solvable_time_file) as solvable_time:
                saved_time = solvable_time.read()
            if saved_time == self.timestamp() and not saved_time == 'static':
                return True

        return False

    def download_from_repository(self, repo_source, target):
        """
        Download given source file from the repository and store
        it as target file

        The repo_source location is used relative to the repository
        location and will be part of a mime type source like:
        `file://repo_path/repo_source`

        :param str repo_source: source file in the repo
        :param str target: file path

        :raises KiwiUriOpenError: if the download fails
        """
        download_link = None
        try:
            download_link = os.sep.join(
                [
                    self._get_mime_typed_uri(),
                    repo_source
                ]
            )
            request = Request(download_link)
            if self.user and self.secret:
                credentials = b64encode(
                    format(':'.join([self.user, self.secret])).encode()
                )
                request.add_header(
                    'Authorization', b'Basic ' + credentials
                )
            location = urlopen(request)
        except Exception as e:
            raise KiwiUriOpenError(
                '{0}: {1} {2}'.format(type(e).__name__, format(e), download_link)
            )
        with open(target, 'wb') as target_file:
            target_file.write(location.read())

    def _get_repomd_xml(self, lookup_path='repodata'):
        """
        Parse repomd.xml file from lookup_path and return an etree
        This method only applies to rpm-md type repositories

        :param str lookup_path: relative path used to find repomd.xml file

        :return: Object with repomd.xml contents

        :rtype: XML etree
        """
        xml_download = NamedTemporaryFile()
        xml_setup_file = os.sep.join([lookup_path, 'repomd.xml'])
        self.download_from_repository(xml_setup_file, xml_download.name)
        return etree.parse(xml_download.name)

    def _get_repomd_xpath(self, xml_data, expression):
        """
        Call the provided xpath expression on the root element
        of the xml_data which must be an XML etree parsed document
        and return the result. This method only applies to
        repomd.xml files of the correct namespaces:

        * http://linux.duke.edu/metadata/repo
        * http://linux.duke.edu/metadata/rpm

        :param object xml_data: An XML etree object of a parsed XML file.
        :param str expression: An xpath expression to filder xml_data.

        :return: Elements matching the xpath expression

        :rtype: list
        """
        namespace_map = dict(
            repo='http://linux.duke.edu/metadata/repo',
            rpm='http://linux.duke.edu/metadata/rpm'
        )
        return xml_data.getroot().xpath(
            expression, namespaces=namespace_map
        )

    def _setup_repository_metadata(self):
        """
        Download all relevant repository metadata and create
        intermediate solvables from the result. The metadata structure
        depends on the type of the repository and must be implemented
        in the specialized Solver Repository classes.
        """
        raise NotImplementedError

    def _create_solvables(self, metadata_dir, tool):
        """
        Create intermediate (before merge) SAT solvables from the
        data given in the metadata_dir and store the result in the
        temporary repository_solvable_dir. The given tool must
        match the solvable data structure. There are the following
        tools to create a solvable from repository metadata:

        * rpmmd2solv
          solvable from repodata files

        * susetags2solv
          solvable from SUSE (yast2) repository files

        * comps2solv
          solvable from RHEL component files

        * rpms2solv
          solvable from rpm header files

        :param str metadata_dir: path name
        :param str tool: one of the above tools
        """
        if not self.repository_solvable_dir:
            self.repository_solvable_dir = mkdtemp(prefix='solvable_dir.')

        if tool == 'rpms2solv':
            # solvable is created from a bunch of rpm files
            bash_command = [
                tool, os.sep.join([metadata_dir, '*.rpm']),
                '>', self._get_random_solvable_name()
            ]
            Command.run(['bash', '-c', ' '.join(bash_command)])
        else:
            # each file in the metadata_dir is considered a valid
            # solvable for the selected solv tool
            for source in glob.iglob('/'.join([metadata_dir, '*'])):
                bash_command = [
                    'gzip', '-cd', '--force', source, '|', tool,
                    '>', self._get_random_solvable_name()
                ]
                Command.run(['bash', '-c', ' '.join(bash_command)])

    def _merge_solvables(self, target_dir):
        """
        Merge all intermediate SAT solvables into one and store
        the result in the given target_dir. In addition an
        info file containing the repo url and a timestamp file
        is created

        :param str target_dir: path name
        """
        if self.repository_solvable_dir:
            solvable = os.sep.join([target_dir, self.uri.alias()])
            bash_command = [
                'mergesolv', '/'.join([self.repository_solvable_dir, '*']),
                '>', solvable
            ]
            Command.run(['bash', '-c', ' '.join(bash_command)])
            with open('.'.join([solvable, 'info']), 'w') as solvable_info:
                solvable_info.write(''.join([self.uri.uri, os.linesep]))
            with open('.'.join([solvable, 'timestamp']), 'w') as solvable_time:
                solvable_time.write(self.timestamp())
            return solvable

    def _cleanup(self):
        """
        Delete all temporary directories
        """
        for metadata_dir in self.repository_metadata_dirs:
            Path.wipe(metadata_dir)

        if self.repository_solvable_dir:
            Path.wipe(self.repository_solvable_dir)

        self._init_temporary_dir_names()

    def _get_mime_typed_uri(self):
        """
        Adds `file` scheme for local URIs

        :return: A mime typed URI as string

        :rtype: str
        """
        return self.uri.translate() if self.uri.is_remote() else ''.join(
            ['file://', self.uri.translate()]
        )

    def _init_temporary_dir_names(self):
        """
        Initialize data structures to store temporary directory names
        required to hold the repository metadata and solvable files
        until the final repository solvable got created
        """
        self.repository_metadata_dirs = []
        self.repository_solvable_dir = None

    def _create_temporary_metadata_dir(self):
        """
        Create and manage a temporary metadata directory

        :return: the path of the temporary directory just created

        :rtype: str
        """
        metadata_dir = mkdtemp(prefix='metadata_dir.')
        self.repository_metadata_dirs.append(metadata_dir)
        return metadata_dir

    def _get_random_solvable_name(self):
        if self.repository_solvable_dir:
            return '{0}/solvable-{1}{2}{3}{4}'.format(
                self.repository_solvable_dir,
                self._rand(), self._rand(), self._rand(), self._rand()
            )

    def _rand(self):
        return '%02x' % random.randrange(1, 0xfe)

    def __del__(self):
        self._cleanup()
