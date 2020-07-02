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
import sys

# project
from kiwi.logger_color_formatter import ColorFormatter
from kiwi.logger_filter import (
    LoggerSchedulerFilter,
    InfoFilter,
    DebugFilter,
    ErrorFilter,
    WarningFilter
)

from kiwi.exceptions import KiwiLogFileSetupFailed


class Logger(logging.Logger):
    """
    **Extended logging facility based on Python logging**

    :param string name: name of the logger
    """
    def __init__(self, name):
        logging.Logger.__init__(self, name)
        self.console_handlers = {}
        self.logfile = None
        # log INFO to stdout
        self._add_stream_handler(
            'info',
            '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
            [InfoFilter(), LoggerSchedulerFilter()]
        )
        # log WARNING messages to stdout
        self._add_stream_handler(
            'warning',
            '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
            [WarningFilter()]
        )
        # log DEBUG messages to stdout
        self._add_stream_handler(
            'debug',
            '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
            [DebugFilter()]
        )
        # log ERROR messages to stderr
        self._add_stream_handler(
            'error',
            '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
            [ErrorFilter()],
            sys.__stderr__
        )
        self.log_level = self.level

    def getLogLevel(self):
        """
        Return currently used log level

        :return: log level number

        :rtype: int
        """
        return self.log_level

    def setLogLevel(self, level):
        """
        Set custom log level for all console handlers

        :param int level: log level number
        """
        self.log_level = level
        for handler_type in self.console_handlers:
            self.console_handlers[handler_type].setLevel(level)

    def set_color_format(self):
        """
        Set color format for all console handlers
        """
        for handler_type in self.console_handlers:
            message_format = None
            if handler_type == 'debug':
                message_format = \
                    '$LIGHTCOLOR[ %(levelname)-8s]: %(asctime)-8s | %(message)s'
            elif handler_type == 'warning' or handler_type == 'error':
                message_format = \
                    '$COLOR[ %(levelname)-8s]: %(asctime)-8s | %(message)s'

            if message_format:
                self.console_handlers[handler_type].setFormatter(
                    ColorFormatter(message_format, '%H:%M:%S')
                )

    def set_logfile(self, filename):
        """
        Set logfile handler

        :param string filename: logfile file path
        """
        try:
            logfile = logging.FileHandler(
                filename=filename, encoding='utf-8'
            )
            logfile.setFormatter(
                logging.Formatter(
                    '%(levelname)s: %(asctime)-8s | %(message)s', '%H:%M:%S'
                )
            )
            logfile.addFilter(LoggerSchedulerFilter())
            self.addHandler(logfile)
            self.logfile = filename
        except Exception as e:
            raise KiwiLogFileSetupFailed(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def get_logfile(self):
        """
        Return file path name of logfile

        :return: file path

        :rtype: str
        """
        return self.logfile

    def progress(self, current, total, prefix, bar_length=40):
        """
        Custom progress log information. progress information is
        intentionally only logged to stdout and will bypass any
        handlers. We don't want this information to show up in
        the log file

        :param int current: current item
        :param int total: total number of items
        :param string prefix: prefix name
        :param int bar_length: length of progress bar
        """
        try:
            percent = float(current) / total
        except Exception:
            # we don't want the progress to raise an exception
            # In case of any error e.g division by zero the current
            # way out is to skip the progress update
            return
        hashes = '#' * int(round(percent * bar_length))
        spaces = ' ' * (bar_length - len(hashes))
        sys.stdout.write('\r{0}: [{1}] {2}%'.format(
            prefix, hashes + spaces, int(round(percent * 100))
        ))
        if current == 100:
            sys.stdout.write('\n')
        sys.stdout.flush()

    def _add_stream_handler(
        self, handler_type, message_format, message_filter,
        channel=sys.__stdout__
    ):
        handler = logging.StreamHandler(channel)
        handler.setFormatter(
            logging.Formatter(message_format, '%H:%M:%S')
        )
        for rule in message_filter:
            handler.addFilter(rule)
        self.addHandler(handler)
        self.console_handlers[handler_type] = handler
