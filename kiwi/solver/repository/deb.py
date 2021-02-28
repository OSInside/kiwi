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
# project
from kiwi.solver.repository.base import SolverRepositoryBase


class SolverRepositoryDeb(SolverRepositoryBase):
    """
    **Class for SAT solvable creation for apt-deb type repositories.**
    """
    def _setup_repository_metadata(self):
        """
        Download repo metadata for apt-deb specific repositories
        and create SAT solvables from all solver relevant files
        """
        # Download Packages metadata for the deb2solv solvable
        # creation. This includes the files named Packages.gz in
        # the repo definition
        deb_dir = self._create_temporary_metadata_dir()
        self._get_deb_packages(download_dir=deb_dir)
        self._create_solvables(
            deb_dir, 'deb2solv'
        )
