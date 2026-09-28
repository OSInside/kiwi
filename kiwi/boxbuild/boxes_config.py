# Copyright (c) 2020 SUSE Software Solutions Germany GmbH.  All rights reserved.
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
import logging
import yaml
from cerberus import Validator
from typing import (
    List, Dict
)

# project
from kiwi.boxbuild.boxes_config_schema import schema
from kiwi.boxbuild.defaults import BoxBuildDefaults

from kiwi.exceptions import KiwiBoxConfigError

log = logging.getLogger('kiwi')


class BoxesConfig:
    """
    **Implements reading of the boxes config file:**

    kiwi_boxed_plugin.yml

    The KIWI box configuration file is a yaml formatted file
    containing information about available virtual disk images
    and containers usable as build boxes
    """
    def __init__(self) -> None:
        self.config_data = {}
        config_file = BoxBuildDefaults.get_box_config_file()
        log.info('Reading boxes config file: {0}'.format(config_file))
        try:
            with open(config_file, 'r') as config:
                self.config_data = yaml.safe_load(config)
        except Exception as issue:
            raise KiwiBoxConfigError(issue)
        validator = Validator(schema)
        validator.validate(self.config_data, schema)
        if validator.errors:
            raise KiwiBoxConfigError(
                'Failed to validate {0}: {1}'.format(
                    config_file, validator.errors
                )
            )

    def get_config(self) -> List[Dict]:
        """
        Return config data dictionary
        """
        return self.config_data.get('box') or []

    def dump_config(self) -> str:
        """
        Return config dump as pretty string for the console
        """
        config_dump = ''
        box_dict = self.config_data.get('box') or {}
        if box_dict:
            config_dump = yaml.dump(box_dict)
        return config_dump
