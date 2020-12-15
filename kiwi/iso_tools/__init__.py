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
from kiwi.exceptions import KiwiIsoToolError
from kiwi.runtime_config import RuntimeConfig


class IsoTools(metaclass=ABCMeta):
    """
    **IsoTools factory**
    """
    @abstractmethod
    def __init__(self) -> None:
        return None  # pragma: no cover

    @staticmethod
    def new(source_dir):
        name_map = {
            'xorriso': 'XorrIso',
            'cdrtools': 'CdrTools'
        }
        runtime_config = RuntimeConfig()
        tool = runtime_config.get_iso_tool_category()
        try:
            iso_tool = importlib.import_module(
                'kiwi.iso_tools.{}'.format(tool)
            )
            module_name = 'IsoTools{}'.format(name_map[tool])
            return iso_tool.__dict__[module_name](source_dir)
        except Exception:
            raise KiwiIsoToolError(
                'No support for {} tool available'.format(tool)
            )
