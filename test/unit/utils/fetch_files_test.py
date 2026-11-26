import io
import requests
from pytest import raises
from unittest.mock import Mock, MagicMock, call, patch

from kiwi.utils.fetch_files import FetchFiles
from kiwi.exceptions import KiwiUriOpenError


class TestFetchFiles:
    def setup(self):
        self.fetcher = FetchFiles()

    def setup_method(self, cls):
        self.setup()

    @patch('kiwi.utils.fetch_files.TransferSpeedColumn')
    @patch('kiwi.utils.fetch_files.TimeRemainingColumn')
    @patch('kiwi.utils.fetch_files.TaskProgressColumn')
    @patch('kiwi.utils.fetch_files.BarColumn')
    @patch('kiwi.utils.fetch_files.TextColumn')
    @patch('kiwi.utils.fetch_files.Progress')
    @patch('kiwi.utils.fetch_files.requests')
    def test_wget(
        self,
        mock_requests,
        mock_Progress,
        mock_TextColumn,
        mock_BarColumn,
        mock_TaskProgressColumn,
        mock_TimeRemainingColumn,
        mock_TransferSpeedColumn,
    ):
        response = Mock()
        response.headers.get.return_value = 8
        response.iter_content.return_value = [b'data', b'', b'more']
        mock_requests.request.return_value = response
        progress = mock_Progress.return_value.__enter__.return_value
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.fetcher.wget('http://foo', 'bar')
            mock_open.assert_called_once_with('bar', 'wb')
            assert file_handle.write.call_args_list == [
                call(b'data'),
                call(b'more'),
            ]
        mock_TextColumn.assert_called_once_with('Loading:')
        mock_Progress.assert_called_once_with(
            mock_TextColumn.return_value,
            mock_BarColumn.return_value,
            mock_TaskProgressColumn.return_value,
            mock_TimeRemainingColumn.return_value,
            mock_TransferSpeedColumn.return_value,
        )
        progress.add_task.assert_called_once_with('Loading', total=8)
        # the progress advances by the size of each written chunk
        assert progress.update.call_args_list == [
            call(progress.add_task.return_value, advance=4),
            call(progress.add_task.return_value, advance=4),
        ]

    @patch('kiwi.utils.fetch_files.TransferSpeedColumn')
    @patch('kiwi.utils.fetch_files.DownloadColumn')
    @patch('kiwi.utils.fetch_files.TextColumn')
    @patch('kiwi.utils.fetch_files.Progress')
    @patch('kiwi.utils.fetch_files.requests.request')
    def test_wget_unknown_length(
        self,
        mock_request,
        mock_Progress,
        mock_TextColumn,
        mock_DownloadColumn,
        mock_TransferSpeedColumn,
    ):
        response = Mock()
        response.headers.get.return_value = None
        response.iter_content.return_value = [b'data']
        mock_request.return_value = response
        progress = mock_Progress.return_value.__enter__.return_value
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value = MagicMock(spec=io.IOBase)
            file_handle = mock_open.return_value.__enter__.return_value
            self.fetcher.wget('http://foo', 'bar')
            file_handle.write.assert_called_once_with(b'data')
        # without the content size, the downloaded size is shown
        mock_Progress.assert_called_once_with(
            mock_TextColumn.return_value,
            mock_DownloadColumn.return_value,
            mock_TransferSpeedColumn.return_value,
        )
        progress.add_task.assert_called_once_with('Loading', total=None)

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
