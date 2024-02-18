from unittest.mock import (
    patch, call
)

import unittest.mock as mock

from kiwi.filesystem.ext2 import FileSystemExt2


class TestFileSystemExt2:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.ext2 = FileSystemExt2(provider, 'root_dir')
        self.ext2.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('kiwi.filesystem.ext2.Command.run')
    def test_create_on_device(self, mock_command):
        self.ext2.create_on_device('label', 100, uuid='uuid')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkfs.ext2', '-L', 'label', '-U', 'uuid', '/dev/foo', '100'])

    @patch('kiwi.filesystem.ext2.Command.run')
    def test_set_uuid(self, mock_command):
        self.ext2.set_uuid()
        assert mock_command.call_args_list == [
            call(['e2fsck', '-y', '-f', '/dev/foo'], raise_on_error=False),
            call(['tune2fs', '-f', '-U', 'random', '/dev/foo'])
        ]
