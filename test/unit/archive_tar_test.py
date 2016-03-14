
from mock import patch

import mock

from .test_helper import *

from kiwi.archive.tar import ArchiveTar


class TestArchiveTar(object):
    def setup(self):
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
                '--xattrs', '-c', '-f', 'foo.tar', 'foo', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    def test_create_from_dir_with_excludes(self, mock_command):
        archive = ArchiveTar('foo.tar', False)
        archive.create('source-dir', ['foo', 'bar'])
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir', '--xattrs', '-c', '-f', 'foo.tar',
                '.', '--exclude', './foo', '--exclude', './bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_xz_compressed(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive.create_xz_compressed('source-dir')
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir',
                '--xattrs', '-c', '-J', '-f', 'foo.tar.xz', 'foo', 'bar'
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
            ['tar', '-C', 'source-dir', '--xattrs', '-c', '-f', 'foo.tar', 'bar']
        )
