from unittest.mock import patch

import unittest.mock as mock

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

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('kiwi.filesystem.btrfs.Command.run')
    def test_create_on_device(self, mock_command):
        self.btrfs.create_on_device('label', 100, uuid='uuid')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == call(
            [
                'mkfs.btrfs', '-L', 'label', '-U', 'uuid',
                '--byte-count', '102400', '/dev/foo'
            ]
        )

    @patch('kiwi.filesystem.btrfs.Command.run')
    def test_set_uuid(self, mock_command):
        self.btrfs.set_uuid()
        mock_command.assert_called_once_with(
            ['btrfstune', '-f', '-u', '/dev/foo']
        )
