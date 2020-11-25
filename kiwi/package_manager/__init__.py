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
import logging

# project
from kiwi.exceptions import KiwiPackageManagerSetupError

log = logging.getLogger('kiwi')


class PackageManager(metaclass=ABCMeta):
    """
    **Package manager factory**

    :param object repository: instance of :class:`Repository`
    :param str package_manager: package manager name
    :param list custom_args: custom package manager arguments list

    :raises KiwiPackageManagerSetupError: if the requested package manager
        type is not supported
    :return: package manager

    :rtype: PackageManagerBase subclass
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(
        repository: object, package_manager_name: str,
        custom_args: List=None  # noqa: E252
    ):
        name_map = {
            'zypper': ['zypper', 'Zypper'],
            'dnf': ['dnf', 'Dnf'],
            'yum': ['dnf', 'Dnf'],
            'microdnf': ['microdnf', 'MicroDnf'],
            'pacman': ['pacman', 'Pacman'],
            'apt-get': ['apt', 'Apt']
        }
        try:
            (module_namespace, module_name) = name_map[package_manager_name]
            package_manager = importlib.import_module(
                'kiwi.package_manager.{0}'.format(module_namespace)
            )
            module_name = 'PackageManager{0}'.format(module_name)
            manager = package_manager.__dict__[module_name](
                repository, custom_args
            )
        except Exception as issue:
            raise KiwiPackageManagerSetupError(
                'Support for package manager {0} not implemented {1}'.format(
                    package_manager_name, issue
                )
            )
        log.info(
            'Using package manager backend: {0}'.format(package_manager_name)
        )
        return manager
