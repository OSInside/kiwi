
from mock import patch

import mock

from .test_helper import *

from kiwi.exceptions import *
from kiwi.filesystem.squashfs import FileSystemSquashFs


class TestFileSystemSquashfs(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.squashfs = FileSystemSquashFs(mock.Mock(), 'root_dir')

    @patch('kiwi.filesystem.squashfs.Command.run')
    def test_create_on_file(self, mock_command):
        self.squashfs.create_on_file('myimage', 'label')
        mock_command.assert_called_once_with(
            ['mksquashfs', 'root_dir', 'myimage', '-noappend', '-comp', 'xz']
        )

    @patch('kiwi.filesystem.squashfs.Command.run')
    def test_create_on_file_exclude_data(self, mock_command):
        self.squashfs.create_on_file('myimage', 'label', ['foo'])
        mock_command.assert_called_once_with(
            [
                'mksquashfs', 'root_dir', 'myimage',
                '-noappend', '-comp', 'xz', '-e', 'foo'
            ]
        )
