import logging
from pytest import fixture
from unittest.mock import patch
from kiwi.utils.output import DataOutput
import json
import unittest.mock as mock


class TestDataOutput:
    @fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def setup(self):
        test_data = {
            'some-name': 'some-data'
        }
        self.expected_out = json.dumps(
            test_data, sort_keys=True, indent=4, separators=(',', ': ')
        )
        self.out = DataOutput(test_data)

    def setup_method(self, cls):
        self.setup()

    @patch('sys.stdout')
    def test_display(self, mock_stdout):
        self.out.display()
        mock_stdout.write.assert_any_call(self.expected_out)

    def test_display_file(self):
        with self._caplog.at_level(logging.INFO):
            with patch('builtins.open', create=True) as mock_open:
                file_handle = mock_open.return_value.__enter__.return_value
                DataOutput.display_file('some-file', 'some-message')
                mock_open.assert_called_once_with('some-file')
                file_handle.read.assert_called_once_with()

    @patch('sys.stdout')
    @patch('os.system')
    @patch('kiwi.utils.output.Temporary.new_file')
    def test_display_color(self, mock_temp, mock_system, mock_stdout):
        out_file = mock.Mock()
        out_file.name = 'tmpfile'
        mock_temp.return_value = out_file
        self.out.style = 'color'
        self.out.color_json = True
        self.out.display()
        mock_system.assert_called_once_with(
            'cat tmpfile | pjson'
        )

    @patch('sys.stdout')
    def test_display_color_no_pjson(self, mock_stdout):
        self.out.style = 'color'
        self.out.color_json = False
        with self._caplog.at_level(logging.WARNING):
            self.out.display()
            assert 'pjson for color output not installed' in self._caplog.text
            assert 'run: pip install pjson' in self._caplog.text
