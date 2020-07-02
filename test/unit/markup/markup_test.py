from mock import patch

from kiwi.markup import Markup

from kiwi.exceptions import KiwiAnyMarkupPluginError


class TestMarkup:
    @patch('kiwi.markup.MarkupAny')
    def test_MarkupAny(self, mock_MarkupAny):
        Markup('description')
        mock_MarkupAny.assert_called_once_with('description')

    @patch('kiwi.markup.MarkupXML')
    @patch('kiwi.markup.MarkupAny')
    def test_MarkupXML(self, mock_MarkupAny, mock_MarkupXML):
        mock_MarkupAny.side_effect = KiwiAnyMarkupPluginError('load-error')
        Markup('description')
        mock_MarkupXML.assert_called_once_with('description')
