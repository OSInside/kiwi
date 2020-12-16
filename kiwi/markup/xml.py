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
# project
from kiwi.markup.base import MarkupBase

from kiwi.exceptions import KiwiMarkupConversionError


class MarkupXML(MarkupBase):
    """
    **Implements plain XML markup handling**
    """
    def get_xml_description(self) -> str:
        """
        Return XML description file name

        :return: file path name

        :rtype: string
        """
        return self.apply_xslt_stylesheets(
            self.description
        )

    def get_yaml_description(self) -> str:
        """
        Conversion into YAML format not supported by base XML markup
        """
        raise KiwiMarkupConversionError(
            'Conversion to YAML not supported, install anymarkup module'
        )
