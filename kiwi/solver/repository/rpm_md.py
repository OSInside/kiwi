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


class SolverRepositoryRpmMd(SolverRepositoryBase):
    """
    **Class for SAT solvable creation for rpm-md type repositories.**
    """
    def _setup_repository_metadata(self):
        """
        Download repo metadata for rpm-md specific repositories
        and create SAT solvables from all solver relevant files
        """
        # Download rpm-md metadata for the rpmmd2solv solvable
        # creation. This includes the files marked as primary
        # and pattern in the repo definition
        rpm_md_dir = self._create_temporary_metadata_dir()
        rpm_md_data = self._find_repomd_files(
            ['primary', 'patterns'], 'rpmmd2solv'
        )
        for rpm_md_file in rpm_md_data.metadata_files:
            self.download_from_repository(
                rpm_md_file,
                os.sep.join([rpm_md_dir, os.path.basename(rpm_md_file)])
            )
        self._create_solvables(
            rpm_md_dir, rpm_md_data.solv_tool
        )

        # Download rpm-md metadata for the comps2solv solvable
        # creation. This includes the files marked as group_gz
        # This component information is like the SUSE pattern
        # information but for RHEL. In order to allow resolving
        # group id names this information needs to be present
        rpm_comps_dir = self._create_temporary_metadata_dir()
        rpm_comps_data = self._find_repomd_files(
            ['group_gz'], 'comps2solv'
        )
        for rpm_comps_file in rpm_comps_data.metadata_files:
            self.download_from_repository(
                rpm_comps_file,
                os.sep.join([rpm_comps_dir, os.path.basename(rpm_comps_file)])
            )
        self._create_solvables(
            rpm_comps_dir, rpm_comps_data.solv_tool
        )

    def timestamp(self):
        """
        Get timestamp from the first primary metadata

        :return: time value as text

        :rtype: str
        """
        return self._get_repomd_xpath(
            self._get_repomd_xml(),
            'repo:data[@type="primary"]/repo:timestamp'
        )[0].text

    def _find_repomd_files(self, type_list, tool):
        """
        Lookup repodata/repomd.xml and the metadata files for the
        specified type list. Assign the found entries to the given
        tool

        :param list type_list:
            Value of type attribute in the repomd.xml definition
        :param str tool:
            Tool to create a solvable from this data

        :return: str:solv_tool, list:metadata_files

        :rtype: tuple
        """
        result_type = namedtuple(
            'result_type', ['solv_tool', 'metadata_files']
        )
        metadata_files = []
        for metadata_type in type_list:
            metadata_locations = self._get_repomd_xpath(
                self._get_repomd_xml(),
                'repo:data[@type="{0}"]/repo:location'.format(metadata_type)
            )
            for location in metadata_locations:
                metadata_files.append(location.get('href'))

        return result_type(
            solv_tool=tool, metadata_files=metadata_files
        )
