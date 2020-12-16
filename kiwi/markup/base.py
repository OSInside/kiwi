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
from tempfile import NamedTemporaryFile
from lxml import etree

# project
from kiwi.defaults import Defaults


class MarkupBase:
    """
    **Implements base class for Markup interface**

    Attributes

    :param str description: description path or content
    """
    def __init__(self, description: str):
        self.description = description
        self.post_init()

    def post_init(self) -> None:
        """
        Post initialization method
        """
        pass

    def apply_xslt_stylesheets(self, description: str) -> str:
        """
        Apply XSLT style sheet rules to an xml file

        The result of the XSLT processing is stored in a named
        temporary file and returned to the caller

        :param str description: path to an XML description file
        """
        xslt_transform = etree.XSLT(
            etree.parse(Defaults.get_xsl_stylesheet_file())
        )
        self.description_xslt_processed = NamedTemporaryFile(prefix='xslt-')
        with open(self.description_xslt_processed.name, "wb") as xsltout:
            xsltout.write(
                etree.tostring(xslt_transform(etree.parse(description)))
            )
        return self.description_xslt_processed.name

    def get_xml_description(self) -> str:
        """
        Return XML description file name

        Implementation in specialized Markup class
        """
        raise NotImplementedError

    def get_yaml_description(self) -> str:
        """
        Return YAML description file name

        Implementation in specialized Markup class
        """
        raise NotImplementedError
