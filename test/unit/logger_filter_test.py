from collections import namedtuple
import logging

from kiwi.logger_filter import (
    LoggerSchedulerFilter,
    InfoFilter,
    DebugFilter,
    ErrorFilter,
    WarningFilter
)


class TestLoggerSchedulerFilter:
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
            assert self.scheduler_filter.filter(record) is False


class TestInfoFilter:
    def setup(self):
        self.info_filter = InfoFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.INFO)
        assert self.info_filter.filter(record) is True


class TestDebugFilter:
    def setup(self):
        self.debug_filter = DebugFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.DEBUG)
        assert self.debug_filter.filter(record) is True


class TestErrorFilter:
    def setup(self):
        self.error_filter = ErrorFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.ERROR)
        assert self.error_filter.filter(record) is True


class TestWarningFilter:
    def setup(self):
        self.error_filter = WarningFilter()

    def test_filter(self):
        MyRecord = namedtuple(
            'MyRecord',
            'levelno'
        )
        record = MyRecord(levelno=logging.WARNING)
        assert self.error_filter.filter(record) is True
