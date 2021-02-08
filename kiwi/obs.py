# Copyright (c) 2021 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
from lxml import etree
import requests
from requests.auth import HTTPBasicAuth
from tempfile import NamedTemporaryFile
from typing import List

# project
from kiwi.xml_state import XMLState
from kiwi.runtime_config import RuntimeConfig
from kiwi.solver.repository.base import SolverRepositoryBase
from kiwi.system.uri import Uri
from kiwi.command import Command

from kiwi.exceptions import (
    KiwiUriOpenError,
    KiwiOBSBuildInfoError,
    KiwiOBSProjectError,
    KiwiOBSSourceError
)

log = logging.getLogger('kiwi')


class OBS:
    """
    **Implements methods to access the Open Build Service API**
    """
    def __init__(
        self, image_path: str, user: str, password: str,
        ssl_verify: bool, profiles: List[str], arch: str, repo: str
    ):
        """
        Initialize OBS API access for a given project and package

        :param str image_path: OBS project/package path
        :param str user: OBS account user name
        :param str password: OBS account password
        :param list profiles: OBS image multibuild profile list
        :param str arch: OBS architecture
        :param str repo: OBS image package build repository name
        :param str api_server:
            OBS api server to use, defaults to https://api.opensuse.org/build
        """
        runtime_config = RuntimeConfig()
        try:
            (self.project, self.package) = image_path.split(os.sep)
        except ValueError:
            raise KiwiOBSProjectError(f'Invalid image path: {image_path}')
        self.user = user
        self.profile = profiles[0] if profiles else None
        self.password = password
        self.ssl_verify = ssl_verify or True
        self.arch = arch or 'x86_64'
        self.repo = repo or 'images'
        self.api_server = runtime_config.get_obs_api_server_url()

    def fetch_obs_image(self, checkout_dir) -> str:
        """
        Fetch image description from the obs project

        :return: temp local path to image description

        :return: path to local image checkout

        :rtype: str
        """
        log.info('Checking out OBS project:')
        if os.path.exists(checkout_dir):
            raise KiwiOBSSourceError(
                f'OBS source checkout dir: {checkout_dir!r} already exists'
            )
        log.info(f'--> {self.project}/{self.package}')
        package_link = os.sep.join(
            [
                self.api_server, 'source',
                self.project, self.package
            ]
        )
        request = self._create_request(package_link)
        package_source_xml_tree = OBS._import_xml_request(request)
        package_source_contents = package_source_xml_tree.getroot().xpath(
            '/directory/entry'
        )
        if not package_source_contents:
            raise KiwiOBSSourceError(
                f'OBS source for {self.package!r} package is empty'
            )
        source_files = []
        for entry in package_source_contents:
            source_files.append(entry.get('name'))

        if '_service' in source_files:
            raise KiwiOBSSourceError(
                f'OBS source for {self.package!r} package is a source service'
            )
        Command.run(['mkdir', '-p', checkout_dir])
        for source_file in source_files:
            log.info(f'--> {source_file}')
            request = self._create_request(
                os.sep.join([package_link, source_file])
            )
            with open(os.sep.join([checkout_dir, source_file]), 'wb') as fd:
                fd.write(request.content)
        return checkout_dir

    def add_obs_repositories(self, xml_state: XMLState) -> None:
        """
        Add repositories from the obs project to the provided XMLState

        :param XMLState xml_state: XMLState object reference
        """
        if not OBS._delete_obsrepositories_placeholder_repo(xml_state):
            # The repo list does not contain the obsrepositories flag
            # Therefore it's not needed to look for repos in the OBS
            # project configuration
            return None

        package_name = self.package if not self.profile \
            else f'{self.package}:{self.profile}'
        log.info(f'Using OBS repositories from {self.project}/{package_name}')
        buildinfo_link = os.sep.join(
            [
                self.api_server, 'build',
                self.project, self.repo, self.arch,
                package_name, '_buildinfo'
            ]
        )
        request = self._create_request(buildinfo_link)
        buildinfo_xml_tree = OBS._import_xml_request(request)
        repo_paths = buildinfo_xml_tree.getroot().xpath(
            '/buildinfo/path'
        )
        if not repo_paths:
            raise KiwiOBSBuildInfoError(
                f'OBS buildinfo for {package_name} has no repo paths'
            )
        repo_prio_ascending = 0
        repo_prio_descending = 501
        repo_alias = None
        for repo_path in repo_paths:
            repo_url = repo_path.get('url')
            if not repo_url:
                repo_url = 'obs://{0}/{1}'.format(
                    repo_path.get('project'), repo_path.get('repository')
                )
            if repo_url:
                log.info(f'OBS Repo: {repo_url}')
                try:
                    repo_uri = Uri(repo_url)
                    repo_url = repo_uri.translate(
                        check_build_environment=False
                    )
                    request = requests.get(repo_url)
                    request.raise_for_status()
                except Exception as issue:
                    log.warn(
                        f'--> Unreachable repo ignored: {issue}'
                    )
                    continue

                repo_check = SolverRepositoryBase(repo_uri)
                repo_type = repo_check.get_repo_type()
                if not repo_type:
                    log.warn('--> Unknown repo type ignored')
                    continue

                if repo_type == 'rpm-md':
                    repo_prio_ascending += 1
                    repo_prio = repo_prio_ascending
                else:
                    repo_prio_descending -= 1
                    repo_prio = repo_prio_descending

                log.info('--> OK')
                xml_state.add_repository(
                    repo_url, repo_type, repo_alias, f'{repo_prio}'
                )

    def _create_request(self, url):
        try:
            request = requests.get(
                url, auth=HTTPBasicAuth(self.user, self.password),
                verify=self.ssl_verify
            )
            request.raise_for_status()
        except Exception as issue:
            raise KiwiUriOpenError(
                f'{type(issue).__name__}: {issue}'
            )
        return request

    @staticmethod
    def _delete_obsrepositories_placeholder_repo(xml_state):
        """
        Delete repository sections which uses the obsrepositories
        placeholder repo and keep the rest for the configured profiles

        :return:
            Returns True if a placeholder repo got deleted
            otherwise False

        :rtype: bool
        """
        has_obsrepositories = False
        repository_sections_to_keep = []
        repository_sections = xml_state.get_repository_sections()
        for xml_repo in repository_sections:
            repo_source = xml_repo.get_source().get_path()
            if 'obsrepositories' in repo_source:
                has_obsrepositories = True
            else:
                repository_sections_to_keep.append(xml_repo)
        xml_state.xml_data.set_repository(repository_sections_to_keep)
        return has_obsrepositories

    @staticmethod
    def _import_xml_request(request):
        download = NamedTemporaryFile()
        with open(download.name, 'wb') as request_info:
            request_info.write(request.content)
        return etree.parse(download.name)
