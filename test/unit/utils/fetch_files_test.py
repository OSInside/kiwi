import io
import requests
from pytest import raises
from unittest.mock import Mock, MagicMock, patch

from kiwi.utils.fetch_files import FetchFiles
from kiwi.exceptions import KiwiUriOpenError


class TestFetchFiles:
    def setup(self):
        self.fetcher = FetchFiles()

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.utils.fetch_files.requests')
    @patch('kiwi.utils.fetch_files.progressbar')
    def test_wget(self, mock_progressbar, mock_requests):
        response = Mock()
        response.headers.get.return_value = 4
        response.iter_content.return_value = [b'data']
        mock_requests.request.return_value = response
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.fetcher.wget('http://foo', 'bar')
            mock_open.assert_called_once_with('bar', 'wb')
            file_handle.write.assert_called_once_with(b'data')
            mock_progressbar.ProgressBar.assert_called_once_with(
                maxval=4,
                widgets=[
                    'Loading: ',
                    mock_progressbar.Percentage.return_value,
                    ' ',
                    mock_progressbar.Bar(marker='#', left='[', right=']'),
                    ' ',
                    mock_progressbar.ETA.return_value,
                    ' ',
                    mock_progressbar.FileTransferSpeed.return_value,
                ],
            )

    @patch('kiwi.utils.fetch_files.requests.request')
    @patch('kiwi.utils.fetch_files.progressbar')
    def test_wget_unknown_length(self, mock_progressbar, mock_request):
        response = Mock()
        response.headers.get.return_value = None
        response.iter_content.return_value = [b'data']
        mock_request.return_value = response
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.fetcher.wget('http://foo', 'bar')
            file_handle.write.assert_called_once_with(b'data')
            mock_progressbar.ProgressBar.assert_called_once_with(
                maxval=mock_progressbar.UnknownLength,
                widgets=[
                    'Loading: ',
                    mock_progressbar.FileTransferSpeed.return_value,
                ],
            )

    @patch('kiwi.utils.fetch_files.requests.request')
    def test_wget_http_error(self, mock_request):
        response = Mock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            '404 Client Error: Not Found for url: http://foo'
        )
        mock_request.return_value = response
        with raises(KiwiUriOpenError) as issue:
            self.fetcher.wget('http://foo', 'bar')
        assert 'Download of http://foo failed: HTTPError: 404' in str(
            issue.value
        )

    @patch('kiwi.utils.fetch_files.requests.request')
    def test_wget_connection_error(self, mock_request):
        mock_request.side_effect = requests.exceptions.ConnectionError(
            'Name or service not known'
        )
        with raises(KiwiUriOpenError) as issue:
            self.fetcher.wget('http://foo', 'bar')
        assert 'ConnectionError: Name or service not known' in str(issue.value)
