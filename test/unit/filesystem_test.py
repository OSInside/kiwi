from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.filesystem import FileSystem


class TestFileSystem(object):
    @raises(KiwiFileSystemSetupError)
    def test_filesystem_not_implemented(self):
        FileSystem('foo', mock.Mock(), 'source_dir')

    @patch('kiwi.filesystem.FileSystemExt2')
    def test_filesystem_ext2(self, mock_ext2):
        provider = mock.Mock()
        FileSystem('ext2', provider, 'source_dir')
        mock_ext2.assert_called_once_with(provider, 'source_dir', None)

    @patch('kiwi.filesystem.FileSystemExt3')
    def test_filesystem_ext3(self, mock_ext3):
        provider = mock.Mock()
        FileSystem('ext3', provider, 'source_dir')
        mock_ext3.assert_called_once_with(provider, 'source_dir', None)

    @patch('kiwi.filesystem.FileSystemExt4')
    def test_filesystem_ext4(self, mock_ext4):
        provider = mock.Mock()
        FileSystem('ext4', provider, 'source_dir')
        mock_ext4.assert_called_once_with(provider, 'source_dir', None)

    @patch('kiwi.filesystem.FileSystemXfs')
    def test_filesystem_xfs(self, mock_xfs):
        provider = mock.Mock()
        FileSystem('xfs', provider, 'source_dir')
        mock_xfs.assert_called_once_with(provider, 'source_dir', None)

    @patch('kiwi.filesystem.FileSystemBtrfs')
    def test_filesystem_btrfs(self, mock_btrfs):
        provider = mock.Mock()
        FileSystem('btrfs', provider, 'source_dir')
        mock_btrfs.assert_called_once_with(provider, 'source_dir', None)

    @patch('kiwi.filesystem.FileSystemFat16')
    def test_filesystem_fat16(self, mock_fat16):
        provider = mock.Mock()
        FileSystem('fat16', provider, 'source_dir')
        mock_fat16.assert_called_once_with(provider, 'source_dir', None)

    @patch('kiwi.filesystem.FileSystemFat32')
    def test_filesystem_fat32(self, mock_fat32):
        provider = mock.Mock()
        FileSystem('fat32', provider, 'source_dir')
        mock_fat32.assert_called_once_with(provider, 'source_dir', None)

    @patch('kiwi.filesystem.FileSystemSquashFs')
    def test_filesystem_squashfs(self, mock_squashfs):
        provider = mock.Mock()
        FileSystem('squashfs', provider, 'source_dir')
        mock_squashfs.assert_called_once_with(provider, 'source_dir', None)
