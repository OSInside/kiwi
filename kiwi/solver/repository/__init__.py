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
import importlib
from abc import (
    ABCMeta,
    abstractmethod
)

# project
from kiwi.exceptions import KiwiSolverRepositorySetupError
from kiwi.system.uri import Uri


class SolverRepository(metaclass=ABCMeta):
    """
    **Repository factory for creation of SAT solvables**

    * :param object uri: Instance of :class:`Uri`
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(uri: Uri, user: str = None, secret: str = None):
        name_map = {
            'yast2': ['SolverRepositorySUSE', 'suse'],
            'rpm-md': ['SolverRepositoryRpmMd', 'rpm_md'],
            'rpm-dir': ['SolverRepositoryRpmDir', 'rpm_dir'],
            'apt-deb': ['SolverRepositoryDeb', 'deb']
        }
        try:
            module_name = name_map[uri.repo_type][0]
            module_namespace = name_map[uri.repo_type][1]
            repository = importlib.import_module(
                'kiwi.solver.repository.{0}'.format(module_namespace)
            )
            return repository.__dict__[module_name](
                uri, user, secret
            )
        except Exception as issue:
            raise KiwiSolverRepositorySetupError(
                'Support for {0} solver repotype not implemented: {1}'.format(
                    uri.repo_type, issue
                )
            )
