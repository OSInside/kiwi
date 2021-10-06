import sys
from mock import (
    patch, call
)
from pytest import raises

from kiwi.logger import Logger

from kiwi.exceptions import KiwiLogFileSetupFailed


class TestLogger:
    def setup(self):
        self.log = Logger('kiwi')

    @patch('sys.stdout')
    def test_progress(self, mock_stdout):
        self.log.progress(50, 100, 'foo')
        mock_stdout.write.assert_called_once_with(
            '\rfoo: [####################                    ] 50%'
        )
        mock_stdout.flush.assert_called_once_with()

    def test_progress_raise(self):
        assert self.log.progress(50, 0, 'foo') is None

    @patch('logging.FileHandler')
    def test_set_logfile(self, mock_file_handler):
        self.log.set_logfile('logfile')
        mock_file_handler.assert_called_once_with(
            filename='logfile', encoding='utf-8'
        )
        assert self.log.get_logfile() == 'logfile'

    @patch('logging.StreamHandler')
    def test_set_logfile_to_stdout(self, mock_stream_handler):
        self.log.set_logfile('stdout')
        mock_stream_handler.assert_called_once_with(
            sys.__stdout__
        )
        assert self.log.get_logfile() is None

    @patch('kiwi.logger.ColorFormatter')
    def test_set_color_format(self, mock_color_format):
        self.log.set_color_format()
        assert sorted(mock_color_format.call_args_list) == [
            call(
                '$COLOR[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
                '%H:%M:%S'
            ),
            call(
                '$COLOR[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
                '%H:%M:%S'
            ),
            call(
                '$LIGHTCOLOR[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
                '%H:%M:%S'
            )
        ]

    @patch('logging.FileHandler')
    def test_set_logfile_raise(self, mock_file_handler):
        mock_file_handler.side_effect = KiwiLogFileSetupFailed
        with raises(KiwiLogFileSetupFailed):
            self.log.set_logfile('logfile')

    def test_getLogLevel(self):
        self.log.setLogLevel(42)
        assert self.log.getLogLevel() == 42
