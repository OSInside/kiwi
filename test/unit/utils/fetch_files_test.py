import io
from unittest.mock import (
    Mock, MagicMock, patch
)

from kiwi.utils.fetch_files import FetchFiles


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
            mock_open.assert_called_once_with(
                'bar', 'wb'
            )
            file_handle.write.assert_called_once_with(b'data')
            mock_progressbar.ProgressBar.assert_called_once_with(
                maxval=4,
                widgets=[
                    'Loading: ',
                    mock_progressbar.Percentage.return_value, ' ',
                    mock_progressbar.Bar(marker='#', left='[', right=']'), ' ',
                    mock_progressbar.ETA.return_value, ' ',
                    mock_progressbar.FileTransferSpeed.return_value
                ]
            )
