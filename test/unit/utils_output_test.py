from mock import patch
from kiwi.utils.output import DataOutput
import json
import mock


class TestDataOutput:
    def setup(self):
        test_data = {
            'some-name': 'some-data'
        }
        self.expected_out = json.dumps(
            test_data, sort_keys=True, indent=4, separators=(',', ': ')
        )
        self.out = DataOutput(test_data)

    @patch('sys.stdout')
    def test_display(self, mock_stdout):
        self.out.display()
        mock_stdout.write.assert_any_call(self.expected_out)

    @patch('sys.stdout')
    @patch('os.system')
    @patch('kiwi.utils.output.NamedTemporaryFile')
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
    @patch('kiwi.logger.log.warning')
    def test_display_color_no_pjson(self, mock_warn, mock_stdout):
        self.out.style = 'color'
        self.out.color_json = False
        self.out.display()
        mock_warn.assert_any_call(
            'pjson for color output not installed'
        )
        mock_warn.assert_any_call(
            'run: pip install pjson'
        )
