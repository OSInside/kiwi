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
from .suse import SolverRepositorySUSE
from .rpm_md import SolverRepositoryRpmMd
from .rpm_dir import SolverRepositoryRpmDir

from ...exceptions import KiwiSolverRepositorySetupError


class SolverRepository(object):
    """
    Repository factory for creation of SAT solvables

    Attributes

    * :attr:`repository_type`
        Repository type name

    * :attr:`uri`
        Instance of Uri
    """
    def __new__(self, repository_type, uri):
        if repository_type == 'yast2':
            return SolverRepositorySUSE(uri)
        elif repository_type == 'rpm-md':
            return SolverRepositoryRpmMd(uri)
        elif repository_type == 'rpm-dir':
            return SolverRepositoryRpmDir(uri)
        else:
            raise KiwiSolverRepositorySetupError(
                'Support for %s solver repository type not implemented' %
                repository_type
            )
