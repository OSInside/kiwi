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
from kiwi.solver.repository.suse import SolverRepositorySUSE
from kiwi.solver.repository.rpm_md import SolverRepositoryRpmMd
from kiwi.solver.repository.rpm_dir import SolverRepositoryRpmDir

from kiwi.exceptions import KiwiSolverRepositorySetupError


class SolverRepository(object):
    """
    **Repository factory for creation of SAT solvables**

    * :param object uri: Instance of :class:`Uri`
    """
    def __new__(self, uri, user=None, secret=None):
        if uri.repo_type == 'yast2':
            return SolverRepositorySUSE(uri, user, secret)
        elif uri.repo_type == 'rpm-md':
            return SolverRepositoryRpmMd(uri, user, secret)
        elif uri.repo_type == 'rpm-dir':
            return SolverRepositoryRpmDir(uri, user, secret)
        else:
            raise KiwiSolverRepositorySetupError(
                'Support for %s solver repository type not implemented' %
                uri.repo_type
            )
