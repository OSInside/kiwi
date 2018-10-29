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
from kiwi.runtime_config import RuntimeConfig

from kiwi.exceptions import (
    KiwiOCIArchiveToolError
)


class OCI(object):
    """
    **OCI Factory**
    """
    def __new__(self, container_tag, container_dir=None):
        runtime_config = RuntimeConfig()
        tool_name = runtime_config.get_oci_archive_tool()
        if tool_name == 'umoci':
            return OCIUmoci(container_tag, container_dir)
        else:
            raise KiwiOCIArchiveToolError(
                'No support for {0} tool available'.format(tool_name)
            )
