from lxml import etree
from mock import patch
from pytest import raises

from kiwi.markup.base import MarkupBase

from kiwi.exceptions import (
    KiwiConfigFileFormatNotSupported,
    KiwiDescriptionInvalid,
    KiwiIncludFileNotFoundError
)


class TestMarkupBase:
    def setup(self):
        self.markup = MarkupBase('../data/example_config.xml')

    def test_get_xml_description(self):
        with raises(NotImplementedError):
            self.markup.get_xml_description()

    def test_get_yaml_description(self):
        with raises(NotImplementedError):
            self.markup.get_yaml_description()

    def test_apply_xslt_stylesheets(self):
        assert 'xslt-' in self.markup.apply_xslt_stylesheets(
            '../data/example_config.xml'
        )

    @patch('kiwi.markup.base.etree.parse')
    def test_apply_xslt_stylesheets_nonXML(self, mock_parse):
        mock_parse.side_effect = etree.XMLSyntaxError('not-XML', '<', 1, 1)
        with raises(KiwiConfigFileFormatNotSupported):
            self.markup.apply_xslt_stylesheets(
                'artificial_and_invalid_XML_markup'
            )

    def test_apply_xslt_stylesheets_broken_XML(self):
        markup = MarkupBase('../data/example_include_config.xml')
        with raises(KiwiDescriptionInvalid):
            markup.apply_xslt_stylesheets(
                '../data/example_include_config.xml'
            )

    def test_apply_xslt_stylesheets_missing_include_reference(self):
        markup = MarkupBase(
            '../data/example_include_config_missing_reference.xml'
        )
        with raises(KiwiIncludFileNotFoundError):
            markup.apply_xslt_stylesheets(
                '../data/example_include_config_missing_reference.xml'
            )
