from unittest.mock import patch

import unittest.mock as mock

from kiwi.filesystem.swap import FileSystemSwap


class TestFileSystemSwap:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(return_value='/dev/foo')
        self.swap = FileSystemSwap(provider, 'root_dir')
        self.swap.setup_mountpoint = mock.Mock(return_value='some-mount-point')

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('kiwi.filesystem.swap.Command.run')
    def test_create_on_device(self, mock_command):
        self.swap.create_on_device('label')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == call(
            ['mkswap', '-L', 'label', '/dev/foo']
        )

    @patch('kiwi.filesystem.swap.Command.run')
    def test_create_on_device_reproducible(self, mock_command):
        with patch.dict('os.environ', {'SOURCE_DATE_EPOCH': '0'}):
            self.swap.create_on_device('label')
        mock_command.assert_called_once_with(
            [
                'mkswap',
                '-L',
                'label',
                '-U',
                '2453562e-7073-2098-d091-fd7a04dc5434',
                '/dev/foo',
            ]
        )
