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
import os
import yaml

# project
from .logger import log
from .exceptions import (
    KiwiRuntimeConfigFormatError
)


class RuntimeConfig(object):
    """
    Implements reading of runtime configuration file:

    * ~/.config/kiwi/config.yml

    The KIWI runtime configuration file is a yaml formatted file
    containing information to control the behavior of the tools
    used by KIWI.
    """
    def __init__(self):
        self.config_data = None

        config_file = os.sep.join(
            [self._home_path(), '.config', 'kiwi', 'config.yml']
        )
        if os.path.exists(config_file):
            log.info('Reading runtime config file: {0}'.format(config_file))
            with open(config_file, 'r') as config:
                self.config_data = yaml.load(config)

    def get_xz_options(self):
        return self._get_attribute_list(element='xz', attribute='options')

    def _get_attribute_list(self, element, attribute):
        if self.config_data and element in self.config_data:
            try:
                return self.config_data[element][0][attribute].split()
            except Exception as e:
                raise KiwiRuntimeConfigFormatError(
                    '{error_type}: {error_text}'.format(
                        error_type=type(e).__name__, error_text=format(e)
                    )
                )

    def _home_path(self):
        return os.environ['HOME']
