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
# project
from kiwi.oci_tools.umoci import OCIUmoci
from kiwi.oci_tools.buildah import OCIBuildah
from kiwi.runtime_config import RuntimeConfig

from kiwi.exceptions import (
    KiwiOCIArchiveToolError
)


class OCI:
    """
    **OCI Factory**
    """
    def __new__(self):
        runtime_config = RuntimeConfig()
        tool_name = runtime_config.get_oci_archive_tool()
        if tool_name == 'umoci':
            return OCIUmoci()
        elif tool_name == 'buildah':
            return OCIBuildah()
        else:
            raise KiwiOCIArchiveToolError(
                'No support for {0} tool available'.format(tool_name)
            )
