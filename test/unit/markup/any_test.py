from unittest.mock import patch
from pytest import raises

from kiwi.markup.any import MarkupAny

from kiwi.exceptions import (
    KiwiDescriptionInvalid,
    KiwiAnyMarkupPluginError
)


class TestMarkupXML:
    def setup(self):
        self.markup = MarkupAny('../data/example_config.xml')

    def setup_method(self, cls):
        self.setup()

    @patch('anymarkup_core.parse_file')
    def test_raises_markup_conversion_error(self, mock_anymarkup_parse_file):
        mock_anymarkup_parse_file.side_effect = Exception
        with raises(KiwiDescriptionInvalid):
            MarkupAny('../data/example_config.xml')

    @patch('importlib.import_module')
    def test_raises_anymarkup_not_available(self, mock_importlib):
        mock_importlib.side_effect = Exception
        with raises(KiwiAnyMarkupPluginError):
            MarkupAny('../data/example_config.xml')

    def test_get_xml_description(self):
        assert 'xslt-' in self.markup.get_xml_description()

    def test_get_yaml_description(self):
        assert 'xslt-' in self.markup.get_yaml_description()

    def test_get_toml_description(self):
        assert 'xslt-' in self.markup.get_toml_description()
