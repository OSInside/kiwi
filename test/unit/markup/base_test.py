from lxml import etree
from mock import patch
from pytest import raises

from kiwi.markup.base import MarkupBase

from kiwi.exceptions import (
    KiwiConfigFileFormatNotSupported,
    KiwiConfigSyntaxError
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
                '../data/example_no_xml_config.xml'
            )

    @patch('kiwi.markup.base.etree.parse')
    def test_apply_xslt_stylesheets_syntax_error(self, mock_parse):
        mock_parse.side_effect = etree.XMLSyntaxError('not-XML', '<', 1, 1)
        with raises(KiwiConfigSyntaxError):
            self.markup.apply_xslt_stylesheets(
                '../data/xample_syntaxerror_config.xml'
            )
