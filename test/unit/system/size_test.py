from mock import patch

import mock

from kiwi.system.size import SystemSize


class TestSystemSize:
    def setup(self):
        self.size = SystemSize('directory')

    def test_customize_ext(self):
        self.size.accumulate_files = mock.Mock(
            return_value=10000
        )
        assert self.size.customize(42, 'ext3') == 67

    def test_customize_btrfs(self):
        assert self.size.customize(42, 'btrfs') == 63

    def test_customize_xfs(self):
        assert self.size.customize(42, 'xfs') == 63

    @patch('kiwi.system.size.Command.run')
    def test_accumulate_mbyte_file_sizes(self, mock_command):
        assert isinstance(self.size.accumulate_mbyte_file_sizes(['/foo']), int)
        mock_command.assert_called_once_with(
            [
                'du', '-s', '--apparent-size', '--block-size', '1',
                '--exclude', 'directory/proc',
                '--exclude', 'directory/sys',
                '--exclude', 'directory/dev',
                '--exclude', '/foo', 'directory'
            ]
        )

    @patch('kiwi.system.size.Command.run')
    def test_accumulate_files(self, mock_command):
        assert isinstance(self.size.accumulate_files(), int)
        mock_command.assert_called_once_with(
            ['bash', '-c', 'find directory | wc -l']
        )
