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
import os
from lxml import etree
from urllib.parse import urlparse

# project
from kiwi.utils.temporary import Temporary
from kiwi.defaults import Defaults
from kiwi.exceptions import (
    KiwiConfigFileFormatNotSupported,
    KiwiDescriptionInvalid,
    KiwiIncludFileNotFoundError
)


class MarkupBase:
    """
    **Implements base class for Markup interface**

    Attributes

    :param str description: description path
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
        # Parse the provided description, raising the appropriate
        # exception if parsing fails.
        try:
            parsed_description = etree.parse(description)
        except etree.XMLSyntaxError:
            raise KiwiConfigFileFormatNotSupported(
                'Configuration file could not be parsed. '
                'In case your configuration file is XML it most likely '
                'contains a syntax error. For other formats the '
                'Python anymarkup module is required.'
            )

        xslt_transform_parser = etree.XMLParser()
        xslt_transform_parser.resolvers.add(
            FileResolver(os.path.dirname(self.description))
        )
        xslt_transform = etree.XSLT(
            etree.parse(
                Defaults.get_xsl_stylesheet_file(), xslt_transform_parser
            )
        )
        self.description_xslt_processed = Temporary(
            prefix='kiwi_xslt-'
        ).new_file()
        try:
            with open(self.description_xslt_processed.name, "wb") as xsltout:
                xsltout.write(
                    etree.tostring(
                        xslt_transform(parsed_description), pretty_print=True
                    )
                )
        except etree.XMLSyntaxError as issue:
            raise KiwiDescriptionInvalid(issue)
        except etree.XSLTApplyError as issue:
            raise KiwiDescriptionInvalid(issue)

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


class FileResolver(etree.Resolver):
    def __init__(self, description_dir):
        self.description_dir = description_dir

    def resolve(self, url, pubid, context):
        if url.startswith('this://'):
            url = url.replace('this://', '')
            url = 'dir://{0}'.format(
                os.path.realpath(os.path.join(self.description_dir, url))
            )
        uri = urlparse(url)
        if uri.path and uri.netloc:
            url = ''.join([uri.netloc, uri.path])
        elif uri.path:
            url = uri.path
        if os.path.exists(url):
            return self.resolve_filename(url, context)
        else:
            raise KiwiIncludFileNotFoundError(
                f'include reference {url!r} does not exist'
            )
