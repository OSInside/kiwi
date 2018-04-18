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
import json
import os
from tempfile import NamedTemporaryFile

# project
from kiwi.path import Path
from kiwi.logger import log


class DataOutput(object):
    """
    **Converts dict or list variables to a print friendly json format**

    Output controller for data dictionary. The class expects a
    python dict or list to hold the data to become displayed. So
    far the output format is set to json

    :param data: python dict or list which holds the data
    :type data: dict, list
    :param str style: output style could be either standard or color
    """
    def __init__(self, data, style='standard'):
        self.data = data
        self.style = style
        self.color_json = Path.which('pjson')

    def display(self):
        """
        Show data in json output format and selected style
        """
        self._json()

    def _json(self):
        """
        Show data in json output format and selected style
        """
        if self.style == 'color':
            if self.color_json:
                self._color_json()
            else:
                log.warning('pjson for color output not installed')
                log.warning('run: pip install pjson')
                self._standard_json()
        else:
            self._standard_json()

    def _standard_json(self):
        """
        Show data in plain json output format without any highlighting
        """
        print(
            json.dumps(
                self.data, sort_keys=True, indent=4, separators=(',', ': ')
            )
        )

    def _color_json(self):
        """
        Show data in json output format with nice color highlighting
        """
        out_file = NamedTemporaryFile()
        out_file.write(json.dumps(self.data, sort_keys=True))
        out_file.flush()
        pjson_cmd = ''.join(
            ['cat ', out_file.name, ' | pjson']
        )
        os.system(pjson_cmd)
