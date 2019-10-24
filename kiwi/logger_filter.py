# Copyright (c) 2015 SUSE Linux GmbH.  All rights reserved.
#
# This file is part of kiwi.
#
# kiwi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kiwi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kiwi.  If not, see <http://www.gnu.org/licenses/>
#
import logging


class LoggerSchedulerFilter(logging.Filter):
    """
    **Extended standard logging Filter**
    """
    def filter(self, record):
        """
        Messages from apscheduler scheduler instances are filtered out
        They conflict with console progress information

        :param tuple record: logging message record

        :return: record.name

        :rtype: str
        """
        ignorables = [
            'apscheduler.scheduler',
            'apscheduler.executors.default'
        ]
        return record.name not in ignorables


class InfoFilter(logging.Filter):
    """
    **Extended standard logging Filter**
    """
    def filter(self, record):
        """
        Only messages with record level INFO and WARNING can pass
        for messages with another level an extra handler is used

        :param tuple record: logging message record

        :return: record.name

        :rtype: str
        """
        if record.levelno == logging.INFO:
            return True


class DebugFilter(logging.Filter):
    """
    **Extended standard debug logging Filter**
    """
    def filter(self, record):
        """
        Only messages with record level DEBUG can pass
        for messages with another level an extra handler is used

        :param tuple record: logging message record

        :return: record.name

        :rtype: str
        """
        if record.levelno == logging.DEBUG:
            return True


class ErrorFilter(logging.Filter):
    """
    **Extended standard error logging Filter**
    """
    def filter(self, record):
        """
        Only messages with record level DEBUG can pass
        for messages with another level an extra handler is used

        :param tuple record: logging message record

        :return: record.name

        :rtype: str
        """
        if record.levelno == logging.ERROR:
            return True


class WarningFilter(logging.Filter):
    """
    **Extended standard warning logging Filter**
    """
    def filter(self, record):
        """
        Only messages with record level WARNING can pass
        for messages with another level an extra handler is used

        :param tuple record: logging message record

        :return: record.name

        :rtype: str
        """
        if record.levelno == logging.WARNING:
            return True
