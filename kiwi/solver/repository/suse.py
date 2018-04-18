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
from collections import namedtuple

# project
from kiwi.solver.repository.base import SolverRepositoryBase


class SolverRepositorySUSE(SolverRepositoryBase):
    """
    **Class for SAT solvable creation for SUSE type repositories.**
    """
    def _setup_repository_metadata(self):
        """
        Download repo metadata for SUSE specific repositories and
        create SAT solvables from all solver relevant files
        """
        metadata_dir = self._create_temporary_metadata_dir()
        repo_data = self._find_primary_repository_files()
        for primary_file in repo_data.primary_files:
            self.download_from_repository(
                primary_file,
                os.sep.join([metadata_dir, os.path.basename(primary_file)])
            )
        self._create_solvables(
            metadata_dir, repo_data.solv_tool
        )

    def _find_primary_repository_files(self):
        """
        Lookup repodata/repomd.xml or alternative the packages.gz
        from the suse/setup/descr metadata. For online suse repos
        the repodata metadata exists and is preferred. On media
        like DVD there might be only the suse metadata. Depending
        on the result this also impacts which tool is required to
        create the solv data from the information


        :return: str:solv_tool, list:primary_files

        :rtype: tuple
        """
        result_type = namedtuple(
            'result_type', ['solv_tool', 'primary_files']
        )
        try:
            primary_files = []
            primary_locations = self._get_repomd_xpath(
                self._get_repomd_xml('suse/repodata'),
                'repo:data[@type="primary"]/repo:location'
            )
            for location in primary_locations:
                primary_files.append(
                    os.sep.join(['suse', location.get('href')])
                )
            return result_type(
                solv_tool='rpmmd2solv',
                primary_files=primary_files
            )
        except Exception:
            return result_type(
                solv_tool='susetags2solv',
                primary_files=['suse/setup/descr/packages.gz']
            )
