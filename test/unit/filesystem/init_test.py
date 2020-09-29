from mock import patch
from pytest import raises
from mock import Mock

from kiwi.filesystem import FileSystem

from kiwi.exceptions import KiwiFileSystemSetupError


class TestFileSystem:
    def test_filesystem_not_implemented(self):
        with raises(KiwiFileSystemSetupError):
            FileSystem.new('foo', Mock(), 'root_dir')

    @patch('kiwi.filesystem.ext2.FileSystemExt2')
    def test_filesystem_ext2(self, mock_ext2):
        provider = Mock()
        FileSystem.new('ext2', provider, 'root_dir')
        mock_ext2.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.ext3.FileSystemExt3')
    def test_filesystem_ext3(self, mock_ext3):
        provider = Mock()
        FileSystem.new('ext3', provider, 'root_dir')
        mock_ext3.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.ext4.FileSystemExt4')
    def test_filesystem_ext4(self, mock_ext4):
        provider = Mock()
        FileSystem.new('ext4', provider, 'root_dir')
        mock_ext4.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.xfs.FileSystemXfs')
    def test_filesystem_xfs(self, mock_xfs):
        provider = Mock()
        FileSystem.new('xfs', provider, 'root_dir')
        mock_xfs.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.btrfs.FileSystemBtrfs')
    def test_filesystem_btrfs(self, mock_btrfs):
        provider = Mock()
        FileSystem.new('btrfs', provider, 'root_dir')
        mock_btrfs.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.fat16.FileSystemFat16')
    def test_filesystem_fat16(self, mock_fat16):
        provider = Mock()
        FileSystem.new('fat16', provider, 'root_dir')
        mock_fat16.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.fat32.FileSystemFat32')
    def test_filesystem_fat32(self, mock_fat32):
        provider = Mock()
        FileSystem.new('fat32', provider, 'root_dir')
        mock_fat32.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.squashfs.FileSystemSquashFs')
    def test_filesystem_squashfs(self, mock_squashfs):
        provider = Mock()
        FileSystem.new('squashfs', provider, 'root_dir')
        mock_squashfs.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.clicfs.FileSystemClicFs')
    def test_filesystem_clicfs(self, mock_clicfs):
        provider = Mock()
        FileSystem.new('clicfs', provider, 'root_dir')
        mock_clicfs.assert_called_once_with(provider, 'root_dir', None)

    @patch('kiwi.filesystem.swap.FileSystemSwap')
    def test_filesystem_swap(self, mock_swap):
        provider = Mock()
        FileSystem.new('swap', provider)
        mock_swap.assert_called_once_with(provider, None, None)
