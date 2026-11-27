import sys
import logging
from unittest.mock import patch, Mock
from pytest import raises

from kiwi.logger import Logger
from kiwi.logger_console import ConsoleHandler

from kiwi.exceptions import KiwiLogFileSetupFailed, KiwiLogSocketSetupFailed


class TestLogger:
    def setup(self):
        self.log = Logger('kiwi')

    def setup_method(self, cls):
        self.setup()

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
        mock_socket_handler.assert_called_once_with('socketfile', None)

    @patch('logging.StreamHandler')
    def test_set_logfile_to_stdout(self, mock_stream_handler):
        self.log.set_logfile('stdout')
        mock_stream_handler.assert_called_once_with(sys.__stdout__)
        assert self.log.get_logfile() is None

    def test_console_handlers(self):
        # the console handlers keep their names, setLogLevel uses them
        assert sorted(self.log.log_handlers) == [
            'debug',
            'error',
            'info',
            'warning',
        ]
        assert isinstance(self.log.log_handlers['info'], ConsoleHandler)
        assert self.log.log_handlers['error'].channel == 'stderr'

    def _records(self):
        handler = logging.Handler()
        handler.emit = Mock()
        self.log.addHandler(handler)
        self.log.setLevel(logging.DEBUG)
        return handler.emit

    def test_phase(self):
        emit = self._records()
        self.log.phase('Prepare root system')
        record = emit.call_args.args[0]
        assert record.getMessage() == 'Prepare root system'
        assert record.kiwi_role == 'phase'
        assert self.log.get_tree_position() == (True, 0)

    def test_item(self):
        emit = self._records()
        self.log.item('Type', 'oem')
        self.log.item('Features', 'LVM', checked=False)
        self.log.item('Features', 'Install ISO', checked=True)
        item, unchecked, checked = [
            emit_call.args[0] for emit_call in emit.call_args_list
        ]
        # the plain message is used for the log file
        assert item.getMessage() == 'Type: oem'
        assert item.kiwi_role == 'item'
        assert item.kiwi_key == 'Type'
        assert item.kiwi_value == 'oem'
        assert item.kiwi_checked is None
        assert unchecked.getMessage() == 'Features: [ ] LVM'
        assert unchecked.kiwi_checked is False
        assert checked.getMessage() == 'Features: [x] Install ISO'

    @patch('kiwi.logger.time.monotonic')
    def test_step(self, mock_monotonic):
        mock_monotonic.side_effect = [10.0, 35.0]
        emit = self._records()
        depths = []
        with self.log.step('Installing bootstrap packages'):
            depths.append(self.log.step_depth)
        assert depths == [1]
        assert self.log.step_depth == 0
        start, end = [emit_call.args[0] for emit_call in emit.call_args_list]
        assert start.getMessage() == 'Installing bootstrap packages'
        assert start.kiwi_role == 'step_start'
        # the plain message is used for the log file
        assert end.getMessage() == 'Installing bootstrap packages: done (25s)'
        assert end.kiwi_role == 'step_done'
        assert end.kiwi_title == 'Installing bootstrap packages'
        assert end.kiwi_duration == 25.0

    @patch('kiwi.logger.time.monotonic')
    def test_step_failed(self, mock_monotonic):
        mock_monotonic.side_effect = [10.0, 12.5]
        emit = self._records()
        with raises(KiwiLogFileSetupFailed):
            with self.log.step('Calling config.sh script'):
                raise KiwiLogFileSetupFailed('issue')
        assert self.log.step_depth == 0
        end = emit.call_args.args[0]
        assert end.getMessage() == 'Calling config.sh script: failed (2.5s)'
        assert end.kiwi_role == 'step_failed'

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
            'handler_two': handler_two,
        }
        self.log.setLogLevel(10, except_for=['handler_one'])
        assert not handler_one.setLevel.called
        handler_two.setLevel.assert_called_once_with(10)

        handler_one.reset_mock()
        handler_two.reset_mock()
        self.log.setLogLevel(10, only_for=['handler_one'])
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
