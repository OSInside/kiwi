from mock import patch

import mock

from kiwi.filesystem.btrfs import FileSystemBtrfs


class TestFileSystemBtrfs:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.btrfs = FileSystemBtrfs(provider, 'root_dir')
        self.btrfs.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('kiwi.filesystem.btrfs.Command.run')
    def test_create_on_device(self, mock_command):
        self.btrfs.create_on_device('label')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkfs.btrfs', '-L', 'label', '/dev/foo'])
