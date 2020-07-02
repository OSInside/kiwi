from mock import patch
from collections import namedtuple

from kiwi.logger_color_formatter import ColorFormatter


class TestColorFormatter:
    def setup(self):
        self.color_formatter = ColorFormatter('%(levelname)s: %(message)s')

    @patch('logging.Formatter.format')
    def test_format(self, mock_format):
        MyRecord = namedtuple(
            'MyRecord',
            'levelname'
        )
        record = MyRecord(levelname='INFO')
        mock_format.return_value = 'message'
        self.color_formatter.format(record)
        assert 'message' in self.color_formatter.format(record)
