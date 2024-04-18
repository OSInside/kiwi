from lxml import etree
from unittest.mock import patch
from pytest import raises

from kiwi.markup.base import MarkupBase
from kiwi.xml_description import XMLDescription
from kiwi.xml_state import XMLState

from kiwi.exceptions import (
    KiwiConfigFileFormatNotSupported,
    KiwiDescriptionInvalid,
    KiwiIncludFileNotFoundError
)


class TestMarkupBase:
    def setup(self):
        self.markup = MarkupBase('../data/example_config.xml')

    def setup_method(self, cls):
        self.setup()

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

    def test_apply_xslt_stylesheets_deprecated(self):
        markup = MarkupBase('../data/example_deprecated_schema.xml')
        with raises(KiwiDescriptionInvalid):
            markup.apply_xslt_stylesheets(
                '../data/example_deprecated_schema.xml'
            )

    def test_apply_xslt_stylesheets_missing_include_reference(self):
        markup = MarkupBase(
            '../data/example_include_config_missing_reference.xml'
        )
        with raises(KiwiIncludFileNotFoundError):
            markup.apply_xslt_stylesheets(
                '../data/example_include_config_missing_reference.xml'
            )

    def test_apply_xslt_stylesheets_include_from_image_description_dir(self):
        markup = MarkupBase(
            '../data/example_include_config_from_description_dir.xml'
        )
        xml_description = markup.apply_xslt_stylesheets(
            '../data/example_include_config_from_description_dir.xml'
        )
        description = XMLDescription(xml_description)
        xml_data = description.load()
        state = XMLState(xml_data)
        assert state.xml_data.get_repository()[0].get_source().get_path() == \
            'http://example.com'
