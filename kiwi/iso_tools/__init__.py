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
from kiwi.iso_tools.cdrtools import IsoToolsCdrTools
from kiwi.iso_tools.xorriso import IsoToolsXorrIso
from kiwi.runtime_config import RuntimeConfig


class IsoTools(object):
    """
    **IsoTools factory**
    """
    def __new__(self, source_dir):
        runtime_config = RuntimeConfig()
        if runtime_config.get_iso_tool_category() == 'cdrtools':
            return IsoToolsCdrTools(source_dir)
        else:
            return IsoToolsXorrIso(source_dir)
