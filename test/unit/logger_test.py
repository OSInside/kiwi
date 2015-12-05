from nose.tools import *
from mock import patch
from collections import namedtuple

import nose_helper
import logging

from kiwi.logger import *
from kiwi.exceptions import (
    KiwiLogFileSetupFailed
)


class TestLoggerSchedulerFilter(object):
    def setup(self):
        self.scheduler_filter = LoggerSchedulerFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'name'
        )
        ignorables = [
            'apscheduler.scheduler',
            'apscheduler.executors.default'
        ]
        for ignorable in ignorables:
            record = MyRecord(name=ignorable)
            assert self.scheduler_filter.filter(record) == False


class TestColorFormatter(object):
    def setup(self):
        self.color_formatter = ColorFormatter('%(levelname)s: %(message)s')

    @patch('logging.Formatter.format')
    def test_format(self, mock_format):
        MyRecord = namedtuple(
            'MyRecord',
            'levelname'
        )
        record = MyRecord(levelname='INFO')
        mock_format.return_value = 'message'
        self.color_formatter.format(record)
        assert 'message' in self.color_formatter.format(record)


class TestInfoFilter(object):
    def setup(self):
        self.info_filter = InfoFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.INFO)
        assert self.info_filter.filter(record) == True


class TestDebugFilter(object):
    def setup(self):
        self.debug_filter = DebugFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.DEBUG)
        assert self.debug_filter.filter(record) == True


class TestErrorFilter(object):
    def setup(self):
        self.error_filter = ErrorFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.ERROR)
        assert self.error_filter.filter(record) == True


class TestWarningFilter(object):
    def setup(self):
        self.error_filter = WarningFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.WARNING)
        assert self.error_filter.filter(record) == True


class TestLogger(object):
    @patch('sys.stdout')
    def test_progress(self, mock_stdout):
        log.progress(50, 100, 'foo')
        mock_stdout.write.assert_called_once_with(
            '\rfoo: [####################                    ] 50%'
        )
        mock_stdout.flush.assert_called_once_with()

    def test_progress_raise(self):
        assert log.progress(50, 0, 'foo') == None

    @patch('logging.FileHandler')
    def test_set_logfile(self, mock_file_handler):
        log.set_logfile('logfile')
        mock_file_handler.assert_called_once_with('logfile')

    @raises(KiwiLogFileSetupFailed)
    @patch('logging.FileHandler')
    def test_set_logfile_raise(self, mock_file_handler):
        mock_file_handler.side_effect = KiwiLogFileSetupFailed
        log.set_logfile('logfile')

    def test_getLogLevel(self):
        log.setLogLevel(42)
        assert log.getLogLevel() == 42
