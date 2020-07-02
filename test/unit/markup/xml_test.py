from pytest import raises

from kiwi.markup.xml import MarkupXML

from kiwi.exceptions import KiwiMarkupConversionError


class TestMarkupXML:
    def setup(self):
        self.markup = MarkupXML('../data/example_config.xml')

    def test_get_xml_description(self):
        assert 'xslt-' in self.markup.get_xml_description()

    def test_get_yaml_description(self):
        with raises(KiwiMarkupConversionError):
            self.markup.get_yaml_description()
