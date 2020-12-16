# Copyright (c) 2018 SUSE Linux GmbH.  All rights reserved.
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
from kiwi.runtime_config import RuntimeConfig
from kiwi.exceptions import (
    KiwiOCIArchiveToolError
)


class OCI(metaclass=ABCMeta):
    """
    **OCI Factory**
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new():
        name_map = {
            'umoci': 'Umoci',
            'buildah': 'Buildah'
        }
        runtime_config = RuntimeConfig()
        tool_name = runtime_config.get_oci_archive_tool()
        try:
            oci_tool = importlib.import_module(
                'kiwi.oci_tools.{}'.format(tool_name)
            )
            module_name = 'OCI{}'.format(name_map[tool_name])
            return oci_tool.__dict__[module_name]()
        except Exception:
            raise KiwiOCIArchiveToolError(
                'No support for {0} tool available'.format(tool_name)
            )
