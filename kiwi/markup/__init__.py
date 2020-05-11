# Copyright (c) 2020 SUSE LLC.  All rights reserved.
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

# project
from kiwi.markup.any import MarkupAny
from kiwi.markup.xml import MarkupXML

from kiwi.exceptions import KiwiAnyMarkupPluginError

log = logging.getLogger('kiwi')


class Markup:
    """
    **Markup factory**

    :param string description: path to description file
    :param string xml_content: description data as content string
    """
    def __new__(self, description):
        try:
            markup = MarkupAny(description)
            log.info('Support for multiple markup descriptions available')
        except KiwiAnyMarkupPluginError:
            markup = MarkupXML(description)
            log.info('Support for XML markup available')
        return markup
