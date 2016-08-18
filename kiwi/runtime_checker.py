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
from textwrap import dedent

# project
from .system.uri import Uri
from .defaults import Defaults
from .exceptions import (
    KiwiRuntimeError
)


class RuntimeChecker(object):
    """
    Implements build consistency checks at runtime

    The schema of an image description covers structure and syntax of
    the provided data. The RuntimeChecker provides methods to perform
    further semantic checks which allows to recognize potential build
    or boot problems early.

    * :attr:`xml_state`
        Instance of XMLState
    """
    def __init__(self, xml_state):
        self.xml_state = xml_state

    def check_repositories_configured(self):
        """
        Verify that that there are repositories configured
        """
        if not self.xml_state.get_repository_sections():
            raise KiwiRuntimeError(
                'No repositories configured'
            )

    def check_image_include_repos_http_resolvable(self):
        """
        Verify that all repos marked with the imageinclude attribute
        can be resolved into a http based web URL
        """

        message = dedent('''\n
            Repository: %s is not publicly available.
            Therefore it can't be included into the system image
            repository configuration. Please check the setup of
            the <imageinclude> attribute for this repository.
        ''')

        repository_sections = self.xml_state.get_repository_sections()
        for xml_repo in repository_sections:
            repo_marked_for_image_include = xml_repo.get_imageinclude()

            if repo_marked_for_image_include:
                repo_source = xml_repo.get_source().get_path()
                repo_type = xml_repo.get_type()
                uri = Uri(repo_source, repo_type)
                if not uri.is_remote():
                    raise KiwiRuntimeError(message % repo_source)

    def check_target_directory_not_in_shared_cache(self, target_dir):
        """
        The target directory must be outside of the kiwi shared cache
        directory in order to avoid busy mounts because kiwi bind mounts
        the cache directory into the image root tree to access host
        caching information

        :param string target_dir: path name
        """

        message = dedent('''\n
            Target directory %s conflicts with kiwi's shared cache
            directory %s. This is going to create a busy loop mount.
            Please choose another target directory.
        ''')

        shared_cache_location = Defaults.get_shared_cache_location()
        absolute_target_dir = os.path.abspath(
            os.path.normpath(target_dir)
        ).replace('//', '/')
        if absolute_target_dir.startswith('/' + shared_cache_location):
            raise KiwiRuntimeError(
                message % (target_dir, shared_cache_location)
            )
