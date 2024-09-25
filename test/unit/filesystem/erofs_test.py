from unittest.mock import patch

import unittest.mock as mock

from kiwi.defaults import Defaults
from kiwi.filesystem.erofs import FileSystemEroFs


class TestFileSystemEroFs:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.erofs = FileSystemEroFs(
            mock.Mock(), 'root_dir',
            custom_args={'compression': 'zstd,level=21'}
        )

    @patch('os.path.exists')
    def setup_method(self, cls, mock_exists):
        self.setup()

    @patch('kiwi.filesystem.erofs.Command.run')
    def test_create_on_file(self, mock_command):
        Defaults.set_platform_name('x86_64')
        self.erofs.create_on_file('myimage', 'label')
        mock_command.assert_called_once_with(
            [
                'mkfs.erofs', '-z', 'zstd,level=21',
                '-L', 'label', 'myimage', 'root_dir'
            ]
        )

    @patch('kiwi.filesystem.erofs.Command.run')
    def test_create_on_file_exclude_data(self, mock_command):
        Defaults.set_platform_name('x86_64')
        self.erofs.create_on_file('myimage', 'label', ['foo'])
        mock_command.assert_called_once_with(
            [
                'mkfs.erofs', '-z', 'zstd,level=21',
                '-L', 'label', '--exclude-regex=^foo$',
                'myimage', 'root_dir'
            ]
        )
