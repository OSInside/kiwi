
from mock import patch, call

import mock

from .test_helper import *

from kiwi.archive.tar import ArchiveTar


class TestArchiveTar(object):
    @patch('kiwi.archive.tar.Command.run')
    def setup(self, mock_command):
        command = mock.Mock()
        command.output = 'version 1.27.0'
        mock_command.return_value = command
        self.archive = ArchiveTar('foo.tar')

    @raises(kiwi.exceptions.KiwiArchiveTarError)
    @patch('kiwi.archive.tar.Command.run')
    def test_invalid_tar_command_version(self, mock_command):
        command = mock.Mock()
        command.output = 'version cannot be parsed'
        mock_command.return_value = command
        self.archive = ArchiveTar('foo.tar')

    @patch('kiwi.archive.tar.Command.run')
    def test_extract(self, mock_command):
        self.archive.extract('destination')
        mock_command.assert_called_once_with(
            ['tar', '-C', 'destination', '-x', '-v', '-f', 'foo.tar']
        )

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive.create('source-dir')
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir',
                '--xattrs', '--xattrs-include=*',
                '-c', '-f', 'foo.tar', 'foo', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    def test_append_files(self, mock_command):
        self.archive.append_files('source-dir', ['foo', 'bar'])
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir', '-r',
                '--file=' + self.archive.filename,
                '--xattrs', '--xattrs-include=*',
                'foo', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_with_options(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive.create('source-dir', options=[
            '--fake-option', 'fake_arg'
        ])
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir',
                '--fake-option', 'fake_arg',
                '--xattrs', '--xattrs-include=*',
                '-c', '-f', 'foo.tar', 'foo', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_with_old_tar_version(self, mock_os_dir, mock_command):
        command = mock.Mock()
        command.output = 'version 1.26.1'
        mock_command.return_value = command
        archive = ArchiveTar('foo.tar')
        mock_os_dir.return_value = ['foo', 'bar']
        archive.create('source-dir')
        calls = [
            call(['tar', '--version']),
            call(
                [
                    'tar', '-C', 'source-dir',
                    '-c', '-f', 'foo.tar', 'foo', 'bar'
                ]
            )
        ] 
        mock_command.assert_has_calls(calls)
        assert mock_command.call_count == 2

    @patch('kiwi.archive.tar.Command.run')
    def test_create_from_dir_with_excludes(self, mock_command):
        command = mock.Mock()
        command.output = 'version 1.27.0'
        mock_command.return_value = command
        archive = ArchiveTar('foo.tar', False)
        archive.create('source-dir', ['foo', 'bar'])
        calls = [
            call(['tar', '--version']),
            call(
                [
                    'tar', '-C', 'source-dir', '--xattrs', '--xattrs-include=*',
                    '-c', '-f', 'foo.tar', '.',
                    '--exclude', './foo', '--exclude', './bar'
                ]
            )
        ] 
        mock_command.assert_has_calls(calls)
        assert mock_command.call_count == 2

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_xz_compressed(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive.create_xz_compressed('source-dir')
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir',
                '--xattrs', '--xattrs-include=*',
                '-c', '-J', '-f', 'foo.tar.xz', 'foo', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_gnu_gzip_compressed(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive.create_gnu_gzip_compressed('source-dir')
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir',
                '--format=gnu', '-cSz', '-f', 'foo.tar.gz', 'foo', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_exclude(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive.create('source-dir', ['foo'])
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir', '--xattrs', '--xattrs-include=*',
                '-c', '-f', 'foo.tar', 'bar'
            ]
        )
