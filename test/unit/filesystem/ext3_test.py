from unittest.mock import (
    patch, call
)

import unittest.mock as mock

from kiwi.filesystem.ext3 import FileSystemExt3


class TestFileSystemExt3:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.ext3 = FileSystemExt3(provider, 'root_dir')
        self.ext3.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('kiwi.filesystem.ext3.Command.run')
    def test_create_on_device(self, mock_command):
        self.ext3.create_on_device('label', 100, uuid='uuid')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == \
            call(['mkfs.ext3', '-L', 'label', '-U', 'uuid', '/dev/foo', '100'])

    @patch('kiwi.filesystem.ext3.Command.run')
    def test_set_uuid(self, mock_command):
        self.ext3.set_uuid()
        assert mock_command.call_args_list == [
            call(['e2fsck', '-y', '-f', '/dev/foo'], raise_on_error=False),
            call(['tune2fs', '-f', '-U', 'random', '/dev/foo'])
        ]
