from mock import patch

import mock

from kiwi.filesystem.squashfs import FileSystemSquashFs


class TestFileSystemSquashfs:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.squashfs = FileSystemSquashFs(mock.Mock(), 'root_dir')

    @patch('platform.machine')
    @patch('kiwi.filesystem.squashfs.Command.run')
    def test_create_on_file(self, mock_command, mock_machine):
        mock_machine.return_value = 'x86_64'
        self.squashfs.create_on_file('myimage', 'label')
        mock_command.assert_called_once_with(
            [
                'mksquashfs', 'root_dir', 'myimage', '-noappend',
                '-b', '1M', '-comp', 'xz', '-Xbcj', 'x86'
            ]
        )

    @patch('platform.machine')
    @patch('kiwi.filesystem.squashfs.Command.run')
    def test_create_on_file_exclude_data(self, mock_command, mock_machine):
        mock_machine.return_value = 'ppc64le'
        self.squashfs.create_on_file('myimage', 'label', ['foo'])
        mock_command.assert_called_once_with(
            [
                'mksquashfs', 'root_dir', 'myimage', '-noappend', '-b', '1M',
                '-comp', 'xz', '-Xbcj', 'powerpc', '-wildcards', '-e', 'foo'
            ]
        )

    @patch('platform.machine')
    @patch('kiwi.filesystem.squashfs.Command.run')
    def test_create_on_file_unkown_arch(self, mock_command, mock_machine):
        mock_machine.return_value = 'aarch64'
        self.squashfs.create_on_file('myimage', 'label')
        mock_command.assert_called_once_with(
            [
                'mksquashfs', 'root_dir', 'myimage',
                '-noappend', '-b', '1M', '-comp', 'xz'
            ]
        )

    @patch('kiwi.filesystem.squashfs.Command.run')
    def test_create_on_file_gzip(self, mock_command):
        self.squashfs.custom_args = {
            'compression': 'gzip', 'create_options': []
        }
        self.squashfs.create_on_file('myimage', 'label')
        mock_command.assert_called_once_with(
            [
                'mksquashfs', 'root_dir', 'myimage',
                '-noappend', '-b', '1M', '-comp', 'gzip'
            ]
        )

    @patch('kiwi.filesystem.squashfs.Command.run')
    def test_create_on_file_no_compression(self, mock_command):
        self.squashfs.custom_args = {
            'compression': 'uncompressed', 'create_options': []
        }
        self.squashfs.create_on_file('myimage', 'label')
        mock_command.assert_called_once_with(
            [
                'mksquashfs', 'root_dir', 'myimage', '-noappend',
                '-b', '1M', '-noI', '-noD', '-noF', '-noX'
            ]
        )
