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
from typing import Any
import importlib

# project
from kiwi.utils.temporary import Temporary
from kiwi.markup.base import MarkupBase

from kiwi.exceptions import (
    KiwiDescriptionInvalid,
    KiwiAnyMarkupPluginError
)


class MarkupAny(MarkupBase):
    """
    **Implements markup handling for XML, YAML, JSON and INI**
    """
    def post_init(self) -> None:
        """
        Convert given description file into XML

        The anymarkup module supports auto detection of the given
        input format and can convert YAML, JSON and INI to XML
        """
        try:
            self.anymarkup: Any = importlib.import_module('anymarkup')
        except Exception as issue:
            raise KiwiAnyMarkupPluginError(issue)
        try:
            self.description_markup_processed = Temporary().new_file()
            markup = self.anymarkup.parse_file(
                self.description, force_types=None
            )
            self.anymarkup.serialize_file(
                markup, self.description_markup_processed.name, format='xml'
            )
        except Exception as issue:
            raise KiwiDescriptionInvalid(issue)

    def get_xml_description(self) -> str:
        """
        Return XML description file name

        :return: file path name

        :rtype: str
        """
        return self.apply_xslt_stylesheets(
            self.description_markup_processed.name
        )

    def get_yaml_description(self) -> str:
        """
        Return YAML description file name

        :return: file path name

        :rtype: str
        """
        xml_description_xslt_transformed = self.apply_xslt_stylesheets(
            self.description_markup_processed.name
        )
        markup = self.anymarkup.parse_file(
            xml_description_xslt_transformed, force_types=None
        )
        # The translation to yaml runs from a translation to json first
        # This is done because a direct translation from xml to yaml
        # causes the ordered mapping to be included. See
        # http://yaml.org/type/omap.html. In the context of kiwi this
        # ordering information is however not needed. The order of
        # sections and attributes doesn't play a role. In json no
        # such ordering concept exists and this is way to convert to
        # yaml without the !!omap definitions.
        self.anymarkup.serialize_file(
            markup, xml_description_xslt_transformed, format='json'
        )
        markup = self.anymarkup.parse_file(
            xml_description_xslt_transformed, force_types=None
        )
        self.anymarkup.serialize_file(
            markup, xml_description_xslt_transformed, format='yaml'
        )
        return xml_description_xslt_transformed
