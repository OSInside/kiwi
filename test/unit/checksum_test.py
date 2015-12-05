from nose.tools import *
from mock import patch

import mock

import nose_helper

from kiwi.exceptions import *
from kiwi.checksum import Checksum


class TestChecksum(object):
    @patch('os.path.exists')
    def setup(self, mock_exists):
        mock_exists.return_value = True
        self.checksum = Checksum('some-file')

    @raises(KiwiFileNotFound)
    def test_checksum_file_not_found(self):
        Checksum('some-file')

    @patch('kiwi.checksum.Compress')
    @patch('hashlib.md5')
    @patch('os.path.getsize')
    @patch('__builtin__.open')
    def test_md5_xz(self, mock_open, mock_size, mock_md5, mock_compress):
        compress = mock.Mock()
        digest = mock.Mock()
        digest.hexdigest = mock.Mock(
            return_value='sum'
        )
        compress.get_format = mock.Mock(
            return_value='xz'
        )
        mock_size.return_value = 1343225856
        mock_md5.return_value = digest
        mock_compress.return_value = compress
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.checksum.md5('outfile')

        call = mock_open.call_args_list[0]
        assert mock_open.call_args_list[0] == call('some-file')
        call = mock_open.call_args_list[1]
        assert mock_open.call_args_list[1] == call('outfile', 'w')
        file_mock.write.assert_called_once_with(
            'sum 163968 8192 163968 8192\n'
        )

    @patch('kiwi.checksum.Compress')
    @patch('hashlib.md5')
    @patch('os.path.getsize')
    @patch('__builtin__.open')
    def test_md5(self, mock_open, mock_size, mock_md5, mock_compress):
        compress = mock.Mock()
        digest = mock.Mock()
        digest.hexdigest = mock.Mock(
            return_value='sum'
        )
        compress.get_format = mock.Mock(
            return_value=None
        )
        mock_size.return_value = 1343225856
        mock_md5.return_value = digest
        mock_compress.return_value = compress
        context_manager_mock = mock.Mock()
        mock_open.return_value = context_manager_mock
        file_mock = mock.Mock()
        enter_mock = mock.Mock()
        exit_mock = mock.Mock()
        enter_mock.return_value = file_mock
        setattr(context_manager_mock, '__enter__', enter_mock)
        setattr(context_manager_mock, '__exit__', exit_mock)

        self.checksum.md5('outfile')

        call = mock_open.call_args_list[0]
        assert mock_open.call_args_list[0] == call('some-file')
        call = mock_open.call_args_list[1]
        assert mock_open.call_args_list[1] == call('outfile', 'w')
        file_mock.write.assert_called_once_with(
            'sum 163968 8192\n'
        )
