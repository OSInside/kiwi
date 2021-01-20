from builtins import bytes
import encodings.ascii as encoding
from mock import (
    patch, call, Mock, mock_open
)
from pytest import raises

from kiwi.utils.checksum import Checksum

from kiwi.exceptions import KiwiFileNotFound


class TestChecksum:
    @patch('os.path.exists')
    def setup(self, mock_exists):
        self.ascii = encoding.getregentry().name
        read_results = [bytes(b''), bytes(b'data'), bytes(b''), bytes(b'data')]

        def side_effect(arg):
            print(read_results[0])
            return read_results.pop()

        self.m_open = mock_open()
        self.m_open.return_value.read.side_effect = side_effect

        mock_exists.return_value = True
        self.checksum = Checksum('some-file')

    def test_checksum_file_not_found(self):
        with raises(KiwiFileNotFound):
            Checksum('some-file')

    @patch('os.path.exists')
    def test_matches_checksum_file_does_not_exist(self, mock_exists):
        mock_exists.return_value = False
        assert self.checksum.matches('sum', 'some-file') is False

    @patch('os.path.exists')
    def test_matches(self, mock_exists):
        mock_exists.return_value = True

        self.m_open.return_value.read.side_effect = None
        self.m_open.return_value.read.return_value = 'sum'
        with patch('builtins.open', self.m_open, create=True):
            assert self.checksum.matches('sum', 'some-file') is True

        self.m_open.assert_called_once_with(
            'some-file', encoding=self.ascii
        )

        with patch('builtins.open', self.m_open, create=True):
            assert self.checksum.matches('foo', 'some-file') is False

    @patch('kiwi.path.Path.which')
    @patch('kiwi.utils.checksum.Compress')
    @patch('hashlib.md5')
    @patch('os.path.getsize')
    def test_md5_xz(self, mock_size, mock_md5, mock_compress, mock_which):
        checksum = Mock
        checksum.uncompressed_filename = 'some-file-uncompressed'
        mock_which.return_value = 'factor'
        compress = Mock()
        digest = Mock()
        digest.block_size = 1024
        digest._calculate_hash_hexdigest = Mock(
            return_value=checksum
        )
        digest.hexdigest = Mock(
            return_value='sum'
        )
        compress.get_format = Mock(
            return_value='xz'
        )
        mock_size.return_value = 1343225856
        mock_md5.return_value = digest
        mock_compress.return_value = compress

        with patch('builtins.open', self.m_open, create=True):
            self.checksum.md5('outfile')

        assert self.m_open.call_args_list == [
            call('some-file', 'rb'),
            call('some-file-uncompressed', 'rb'),
            call('outfile', encoding=self.ascii, mode='w')
        ]
        self.m_open.return_value.write.assert_called_once_with(
            'sum 163968 8192 163968 8192\n'
        )

    @patch('kiwi.path.Path.which')
    @patch('kiwi.utils.checksum.Compress')
    @patch('hashlib.md5')
    @patch('os.path.getsize')
    def test_md5(
        self, mock_size, mock_md5, mock_compress, mock_which
    ):
        mock_which.return_value = 'factor'
        compress = Mock()
        digest = Mock()
        digest.block_size = 1024
        digest.hexdigest = Mock(
            return_value='sum'
        )
        compress.get_format = Mock(
            return_value=None
        )
        mock_size.return_value = 1343225856
        mock_md5.return_value = digest
        mock_compress.return_value = compress

        with patch('builtins.open', self.m_open, create=True):
            self.checksum.md5('outfile')

        assert self.m_open.call_args_list == [
            call('some-file', 'rb'),
            call('outfile', encoding=self.ascii, mode='w')
        ]
        self.m_open.return_value.write.assert_called_once_with(
            'sum 163968 8192\n'
        )

    @patch('kiwi.path.Path.which')
    @patch('kiwi.utils.checksum.Compress')
    @patch('hashlib.sha256')
    @patch('os.path.getsize')
    def test_sha256(
        self, mock_size, mock_sha256, mock_compress, mock_which
    ):
        mock_which.return_value = 'factor'
        compress = Mock()
        digest = Mock()
        digest.block_size = 1024
        digest.hexdigest = Mock(
            return_value='sum'
        )
        compress.get_format = Mock(
            return_value=None
        )
        mock_size.return_value = 1343225856
        mock_sha256.return_value = digest
        mock_compress.return_value = compress

        with patch('builtins.open', self.m_open, create=True):
            self.checksum.sha256('outfile')

        assert self.m_open.call_args_list == [
            call('some-file', 'rb'),
            call('outfile', encoding=self.ascii, mode='w')
        ]
        self.m_open.return_value.write.assert_called_once_with(
            'sum 163968 8192\n'
        )

    @patch('hashlib.sha256')
    def test_sha256_plain(self, mock_sha256):
        digest = Mock()
        digest.block_size = 1024
        digest.hexdigest = Mock(
            return_value='sum'
        )
        mock_sha256.return_value = digest

        with patch('builtins.open', self.m_open, create=True):
            assert self.checksum.sha256() == digest.hexdigest.return_value

    @patch('hashlib.md5')
    def test_md5_plain(self, mock_md5):
        digest = Mock()
        digest.block_size = 1024
        digest.hexdigest = Mock(
            return_value='sum'
        )
        mock_md5.return_value = digest

        with patch('builtins.open', self.m_open, create=True):
            assert self.checksum.md5() == digest.hexdigest.return_value
