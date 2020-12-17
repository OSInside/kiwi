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

from kiwi.exceptions import (
    KiwiContainerImageSetupError
)


class ContainerImage(metaclass=ABCMeta):
    """
    **Container Image factory**

    :param string name: container system name
    :param string root_dir: root directory path name
    :param dict custom_args: custom arguments
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(name: str, root_dir: str, custom_args: Dict=None):  # noqa: E252
        name_map = {
            'docker': 'OCI',
            'oci': 'OCI',
            'appx': 'Appx'
        }
        args_map = {
            'docker': [root_dir, 'docker-archive', custom_args],
            'oci': [root_dir, 'oci-archive', custom_args],
            'appx': [root_dir, custom_args]
        }
        try:
            container_image = importlib.import_module(
                'kiwi.container.{}'.format('oci' if name == 'docker' else name)
            )
            module_name = 'ContainerImage{}'.format(name_map[name])
            return container_image.__dict__[module_name](*args_map[name])
        except Exception:
            raise KiwiContainerImageSetupError(
                'Support for {0} container not implemented'.format(name)
            )
