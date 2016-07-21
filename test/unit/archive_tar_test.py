
from mock import patch
from textwrap import dedent

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
        self.archive._does_tar_command_support_xattrs = mock.Mock(return_value=True)
        self.archive.create('source-dir')
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir',
                '--xattrs', '--xattrs-include=*',
                '-c', '-f', 'foo.tar', 'foo', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    def test_create_from_dir_with_excludes(self, mock_command):
        archive = ArchiveTar('foo.tar', False)
        archive._does_tar_command_support_xattrs = mock.Mock(return_value=True)
        archive.create('source-dir', ['foo', 'bar'])
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir', '--xattrs', '--xattrs-include=*',
                '-c', '-f', 'foo.tar', '.',
                '--exclude', './foo', '--exclude', './bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_xz_compressed(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive._does_tar_command_support_xattrs = mock.Mock(return_value=True)
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
        self.archive._does_tar_command_support_xattrs = mock.Mock(return_value=True)
        self.archive.create('source-dir', ['foo'])
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir', '--xattrs', '--xattrs-include=*',
                '-c', '-f', 'foo.tar', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    def test_does_tar_command_support_xattrs_yes(self, mock_command):
        mock_command.return_value.output = dedent("""\
            tar (GNU tar) 1.27.1
            Copyright (C) 2013 Free Software Foundation, Inc.
            blah blah blah
            """)
        mock_command.return_value.returncode = 0
        assert self.archive._does_tar_command_support_xattrs()
        mock_command.assert_called_once_with(['tar', '--version'])

    @patch('kiwi.archive.tar.Command.run')
    def test_does_tar_command_support_xattrs_no(self, mock_command):
        mock_command.return_value.returncode = 0
        mock_command.return_value.output = dedent("""\
            tar (GNU tar) 1.26
            Copyright (C) 2013 Free Software Foundation, Inc.
            blah blah blah
            """)
        assert not self.archive._does_tar_command_support_xattrs()
        mock_command.assert_called_once_with(['tar', '--version'])

    @patch('kiwi.archive.tar.Command.run')
    @raises(EnvironmentError)
    def test_tar_bad_command_raises(self, mock_command):
        mock_command.return_value.returncode = 1
        self.archive._does_tar_command_support_xattrs()

    @patch('kiwi.archive.tar.Command.run')
    @raises(EnvironmentError)
    def test_tar_version_unable_to_parse(self, mock_command):
        mock_command.return_value.returncode = 0
        mock_command.return_value.output = dedent("""\
            bad first line of tar(1) version
            """)
        self.archive._does_tar_command_support_xattrs()

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_when_tar_has_no_xattr_support(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive._does_tar_command_support_xattrs = mock.Mock(return_value=False)
        self.archive.create('source-dir')
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir',
                '-c', '-f', 'foo.tar', 'foo', 'bar'
            ]
        )

    @patch('kiwi.archive.tar.Command.run')
    @patch('os.listdir')
    def test_create_xz_compressed__when_tar_has_no_xattr_support(self, mock_os_dir, mock_command):
        mock_os_dir.return_value = ['foo', 'bar']
        self.archive._does_tar_command_support_xattrs = mock.Mock(return_value=False)
        self.archive.create_xz_compressed('source-dir')
        mock_command.assert_called_once_with(
            [
                'tar', '-C', 'source-dir',
                '-c', '-J', '-f', 'foo.tar.xz', 'foo', 'bar'
            ]
        )
