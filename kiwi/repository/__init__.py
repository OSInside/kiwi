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
from typing import List
from abc import (
    ABCMeta,
    abstractmethod
)

# project
from kiwi.exceptions import KiwiRepositorySetupError


class Repository(metaclass=ABCMeta):
    """
    **Repository factory**

    :param object root_bind: instance of RootBind
    :param str package_manager: package manager name
    :param list custom_args: list of custom package manager arguments
        to setup the repository

    :raises KiwiRepositorySetupError: if package_manager is not supported
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        root_bind: object, package_manager: str,
        custom_args: List=None  # noqa: E252
    ):
        name_map = {
            'zypper': ['zypper', 'Zypper'],
            'dnf': ['dnf', 'Dnf'],
            'microdnf': ['dnf', 'Dnf'],
            'apt': ['apt', 'Apt'],
            'pacman': ['pacman', 'Pacman']
        }
        try:
            repository = importlib.import_module(
                'kiwi.repository.{0}'.format(name_map[package_manager][0])
            )
            module_name = 'Repository{0}'.format(name_map[package_manager][1])
            return repository.__dict__[module_name](
                root_bind, custom_args
            )
        except Exception as issue:
            raise KiwiRepositorySetupError(
                'Support for {0} repository not implemented: {1}'.format(
                    package_manager, issue
                )
            )
