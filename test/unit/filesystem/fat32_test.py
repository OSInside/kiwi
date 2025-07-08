from unittest.mock import patch

import unittest.mock as mock

from kiwi.filesystem.fat32 import FileSystemFat32


class TestFileSystemFat32:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.fat32 = FileSystemFat32(provider, 'root_dir')
        self.fat32.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('kiwi.filesystem.fat32.Command.run')
    def test_create_on_device(self, mock_command):
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            self.fat32.create_on_device(
                'label', 100, uuid='12345678-1234-5678-1234-567812345678'
            )
            call = mock_command.call_args_list[0]
            assert mock_command.call_args_list[0] == call(
                [
                    'mkdosfs', '-F32', '-I', '-n', 'label',
                    '-i', '12345678', '/dev/foo', '100'
                ]
            )
            mock_command.reset_mock()
            self.fat32.create_on_device('label', 100)
            assert mock_command.call_args_list[0] == call(
                [
                    'mkdosfs', '-F32', '-I',
                    '-n', 'label',
                    '-i', '2453562E',
                    '/dev/foo',
                    '100'
                ]
            )

    @patch('kiwi.filesystem.fat32.Command.run')
    def test_set_uuid(self, mock_command):
        self.fat32.set_uuid()
        mock_command.assert_called_once_with(
            ['mlabel', '-n', '-i', '/dev/foo', '::']
        )
