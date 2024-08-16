import sys
from unittest.mock import (
    patch, call, Mock
)
from pytest import raises

from kiwi.logger import Logger

from kiwi.exceptions import (
    KiwiLogFileSetupFailed,
    KiwiLogSocketSetupFailed
)


class TestLogger:
    def setup(self):
        self.log = Logger('kiwi')

    def setup_method(self, cls):
        self.setup()

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

    @patch('kiwi.logger.PlainTextSocketHandler')
    def test_set_log_socket(self, mock_socket_handler):
        self.log.set_log_socket('socketfile')
        mock_socket_handler.assert_called_once_with(
            'socketfile', None
        )

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

    @patch('kiwi.logger.PlainTextSocketHandler')
    def test_set_log_socket_raise(self, mock_socket_handler):
        mock_socket_handler.side_effect = KiwiLogSocketSetupFailed
        with raises(KiwiLogSocketSetupFailed):
            self.log.set_log_socket('socketfile')

    def test_getLogLevel(self):
        self.log.setLogLevel(42)
        assert self.log.getLogLevel() == 42

    def test_setLogLevel(self):
        handler_one = Mock()
        handler_two = Mock()
        self.log.log_handlers = {
            'handler_one': handler_one,
            'handler_two': handler_two
        }
        self.log.setLogLevel(
            10, except_for=['handler_one']
        )
        assert not handler_one.setLevel.called
        handler_two.setLevel.assert_called_once_with(10)

        handler_one.reset_mock()
        handler_two.reset_mock()
        self.log.setLogLevel(
            10, only_for=['handler_one']
        )
        assert not handler_two.setLevel.called
        handler_one.setLevel.assert_called_once_with(10)

        handler_one.reset_mock()
        handler_two.reset_mock()
        self.log.setLogLevel(
            10, except_for=['handler_one'], only_for=['handler_one']
        )
        assert not handler_two.setLevel.called
        handler_one.setLevel.assert_called_once_with(10)

    def test_getLogFlags(self):
        assert self.log.getLogFlags().get('run-scripts-in-screen') is None
        self.log.setLogFlag('run-scripts-in-screen')
        assert self.log.getLogFlags().get('run-scripts-in-screen') is True
