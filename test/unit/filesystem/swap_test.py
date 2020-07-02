from mock import patch

import mock

from kiwi.filesystem.swap import FileSystemSwap


class TestFileSystemSwap:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.swap = FileSystemSwap(provider, 'root_dir')
        self.swap.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('kiwi.filesystem.swap.Command.run')
    def test_create_on_device(self, mock_command):
        self.swap.create_on_device('label')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkswap', '-L', 'label', '/dev/foo'])
