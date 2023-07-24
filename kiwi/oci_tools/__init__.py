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
from abc import (
    ABCMeta,
    abstractmethod
)
from kiwi.oci_tools.base import OCIBase

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
    def new() -> OCIBase:
        tool_name = RuntimeConfig().get_oci_archive_tool()
        if tool_name == "umoci":
            from kiwi.oci_tools.umoci import OCIUmoci
            return OCIUmoci()
        elif tool_name == "buildah":
            from kiwi.oci_tools.buildah import OCIBuildah
            return OCIBuildah()
        else:
            raise KiwiOCIArchiveToolError(
                'No support for {0} tool available'.format(tool_name)
            )
