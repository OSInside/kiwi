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
from typing import Dict

# project
from kiwi.exceptions import (
    KiwiContainerSetupError
)


class ContainerSetup(metaclass=ABCMeta):
    """
        container setup factory
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(name: str, root_dir: str, custom_args: Dict=None):  # noqa: E252
        name_map = {
            'docker': 'Docker',
            'oci': 'OCI',
            'appx': 'Appx'
        }
        try:
            container_setup = importlib.import_module(
                'kiwi.container.setup.{}'.format(name)
            )
            module_name = 'ContainerSetup{}'.format(name_map[name])
            return container_setup.__dict__[module_name](root_dir, custom_args)
        except Exception:
            raise KiwiContainerSetupError(
                'Support for {0} container not implemented'.format(name)
            )
