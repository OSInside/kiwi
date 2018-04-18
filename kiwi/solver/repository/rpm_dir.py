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
import glob

# project
from kiwi.solver.repository.base import SolverRepositoryBase
from kiwi.exceptions import KiwiRpmDirNotRemoteError


class SolverRepositoryRpmDir(SolverRepositoryBase):
    """
    **Class for SAT solvable creation for rpm_dir type repositories.**
    """
    def _setup_repository_metadata(self):
        """
        Download rpms from the repository and create a SAT
        solvable from the rpm header metadata
        """
        if self.uri.is_remote():
            raise KiwiRpmDirNotRemoteError(
                'Only local rpm-dir repositories are supported'
            )

        package_dir = self._create_temporary_metadata_dir()
        for package in glob.iglob('/'.join([self.uri.translate(), '*.rpm'])):
            package_name = os.path.basename(package)
            self.download_from_repository(
                package_name, os.sep.join([package_dir, package_name])
            )
        self._create_solvables(
            package_dir, 'rpms2solv'
        )
