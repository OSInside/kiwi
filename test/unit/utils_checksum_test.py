from mock import call
from mock import patch
import mock

from .test_helper import raises, patch_open

from kiwi.exceptions import KiwiFileNotFound
from kiwi.utils.checksum import Checksum

from builtins import bytes


class TestChecksum(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        self.context_manager_mock = mock.Mock()
        self.file_mock = mock.Mock()
        self.enter_mock = mock.Mock()
        self.exit_mock = mock.Mock()
        self.enter_mock.return_value = self.file_mock
        setattr(self.context_manager_mock, '__enter__', self.enter_mock)
        setattr(self.context_manager_mock, '__exit__', self.exit_mock)

        read_results = [bytes(b''), bytes(b'data')]

        def side_effect(arg):
            return read_results.pop()

        self.file_mock.read.side_effect = side_effect

        mock_exists.return_value = True
        self.checksum = Checksum('some-file')

    @raises(KiwiFileNotFound)
    def test_checksum_file_not_found(self):
        Checksum('some-file')

    @patch('os.path.exists')
    def test_matches_checksum_file_does_not_exist(self, mock_exists):
        mock_exists.return_value = False
        assert self.checksum.matches('sum', 'some-file') is False

    @patch('os.path.exists')
    @patch_open
    def test_matches(self, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_open.return_value = self.context_manager_mock
        self.file_mock.read.side_effect = None
        self.file_mock.read.return_value = 'sum'
        assert self.checksum.matches('sum', 'some-file') is True
        mock_open.assert_called_once_with('some-file')
        assert self.checksum.matches('foo', 'some-file') is False

    @patch('kiwi.path.Path.which')
    @patch('kiwi.utils.checksum.Compress')
    @patch('hashlib.md5')
    @patch('os.path.getsize')
    @patch_open
    def test_md5_xz(
        self, mock_open, mock_size, mock_md5, mock_compress, mock_which
    ):
        checksum = mock.Mock
        checksum.uncompressed_filename = 'some-file-uncompressed'
        mock_which.return_value = 'factor'
        compress = mock.Mock()
        digest = mock.Mock()
        digest.block_size = 1024
        digest._calculate_hash_hexdigest = mock.Mock(
            return_value=checksum
        )
        digest.hexdigest = mock.Mock(
            return_value='sum'
        )
        compress.get_format = mock.Mock(
            return_value='xz'
        )
        mock_open.return_value = self.context_manager_mock
        mock_size.return_value = 1343225856
        mock_md5.return_value = digest
        mock_compress.return_value = compress

        self.checksum.md5('outfile')

        assert mock_open.call_args_list == [
            call('some-file', 'rb'),
            call('some-file-uncompressed', 'rb'),
            call('outfile', 'w')
        ]
        self.file_mock.write.assert_called_once_with(
            'sum 163968 8192 163968 8192\n'
        )

    @patch('kiwi.path.Path.which')
    @patch('kiwi.utils.checksum.Compress')
    @patch('hashlib.md5')
    @patch('os.path.getsize')
    @patch_open
    def test_md5(
        self, mock_open, mock_size, mock_md5, mock_compress, mock_which
    ):
        mock_which.return_value = 'factor'
        compress = mock.Mock()
        digest = mock.Mock()
        digest.block_size = 1024
        digest.hexdigest = mock.Mock(
            return_value='sum'
        )
        compress.get_format = mock.Mock(
            return_value=None
        )
        mock_open.return_value = self.context_manager_mock
        mock_size.return_value = 1343225856
        mock_md5.return_value = digest
        mock_compress.return_value = compress

        self.checksum.md5('outfile')

        assert mock_open.call_args_list == [
            call('some-file', 'rb'),
            call('outfile', 'w')
        ]
        self.file_mock.write.assert_called_once_with(
            'sum 163968 8192\n'
        )

    @patch('kiwi.path.Path.which')
    @patch('kiwi.utils.checksum.Compress')
    @patch('hashlib.sha256')
    @patch('os.path.getsize')
    @patch_open
    def test_sha256(
        self, mock_open, mock_size, mock_sha256, mock_compress, mock_which
    ):
        mock_which.return_value = 'factor'
        compress = mock.Mock()
        digest = mock.Mock()
        digest.block_size = 1024
        digest.hexdigest = mock.Mock(
            return_value='sum'
        )
        compress.get_format = mock.Mock(
            return_value=None
        )
        mock_open.return_value = self.context_manager_mock
        mock_size.return_value = 1343225856
        mock_sha256.return_value = digest
        mock_compress.return_value = compress

        self.checksum.sha256('outfile')

        assert mock_open.call_args_list == [
            call('some-file', 'rb'),
            call('outfile', 'w')
        ]
        self.file_mock.write.assert_called_once_with(
            'sum 163968 8192\n'
        )

    @patch('hashlib.sha256')
    @patch_open
    def test_sha256_plain(self, mock_open, mock_sha256):
        digest = mock.Mock()
        digest.block_size = 1024
        digest.hexdigest = mock.Mock(
            return_value='sum'
        )
        mock_sha256.return_value = digest
        mock_open.return_value = self.context_manager_mock
        assert self.checksum.sha256() == digest.hexdigest.return_value

    @patch('hashlib.md5')
    @patch_open
    def test_md5_plain(self, mock_open, mock_md5):
        digest = mock.Mock()
        digest.block_size = 1024
        digest.hexdigest = mock.Mock(
            return_value='sum'
        )
        mock_md5.return_value = digest
        mock_open.return_value = self.context_manager_mock
        assert self.checksum.md5() == digest.hexdigest.return_value
