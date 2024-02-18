from unittest.mock import (
    patch, call
)

import unittest.mock as mock

from kiwi.filesystem.xfs import FileSystemXfs


class TestFileSystemXfs:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        provider = mock.Mock()
        provider.get_device = mock.Mock(
            return_value='/dev/foo'
        )
        self.xfs = FileSystemXfs(provider, 'root_dir')
        self.xfs.setup_mountpoint = mock.Mock(
            return_value='some-mount-point'
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('kiwi.filesystem.xfs.Command.run')
    def test_create_on_device(self, mock_command):
        self.xfs.create_on_device('label', 100, uuid='uuid')
        call = mock_command.call_args_list[0]
        assert mock_command.call_args_list[0] == call(
            [
                'mkfs.xfs', '-f', '-L', 'label',
                '-m', 'uuid=uuid', '-d', 'size=100k', '/dev/foo'
            ]
        )

    @patch('kiwi.filesystem.xfs.Command.run')
    def test_set_uuid(self, mock_command):
        self.xfs.set_uuid()
        assert mock_command.call_args_list == [
            call(['xfs_repair', '-L', '/dev/foo']),
            call(['xfs_admin', '-U', 'generate', '/dev/foo'])
        ]
