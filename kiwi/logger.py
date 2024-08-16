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
from typing import (
    Dict, Optional, List
)
import logging
from kiwi.logger_socket import PlainTextSocketHandler
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

from kiwi.exceptions import (
    KiwiLogFileSetupFailed,
    KiwiLogSocketSetupFailed
)


class Logger(logging.Logger):
    """
    **Extended logging facility based on Python logging**

    :param str name: name of the logger
    """
    def __init__(self, name: str):
        logging.Logger.__init__(self, name)
        self.log_handlers: Dict = {}
        self.logfile: Optional[str] = None
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
        self.log_flags: Dict[str, bool] = {}

    def getLogLevel(self) -> int:
        """
        Return currently used log level

        :return: log level number

        :rtype: int
        """
        return self.log_level

    def getLogFlags(self) -> Dict[str, bool]:
        """
        Return logging flags

        :return:
            Dictionary with flags and their activation status

        :rtype: dict
        """
        return self.log_flags

    def setLogLevel(
        self, level: int, except_for: List[str] = [], only_for: List[str] = []
    ) -> None:
        """
        Set custom log level for all console handlers

        :param int level: log level number
        :param list except_for:
            set log level to all handlers except for the given list
        :param list only_for:
            set log level to the given handlers only

        if both except_for and only_for handlers are specified,
        the except_for list will be ignored
        """
        self.log_level = level
        if only_for:
            for handler_type in self.log_handlers:
                if handler_type in only_for:
                    self.log_handlers[handler_type].setLevel(level)
            return
        for handler_type in self.log_handlers:
            if handler_type not in except_for:
                self.log_handlers[handler_type].setLevel(level)

    def setLogFlag(self, flag: str, value: bool = True) -> None:
        """
        Set logging flag for further properties of the logging facility
        Available flags are:

        * run-scripts-in-screen

        :param str flag: name
        """
        self.log_flags[flag] = value

    def set_color_format(self) -> None:
        """
        Set color format for all console handlers
        """
        for handler_type in self.log_handlers:
            message_format = None
            if handler_type == 'debug':
                message_format = \
                    '$LIGHTCOLOR[ %(levelname)-8s]: %(asctime)-8s | %(message)s'
            elif handler_type == 'warning' or handler_type == 'error':
                message_format = \
                    '$COLOR[ %(levelname)-8s]: %(asctime)-8s | %(message)s'

            if message_format:
                self.log_handlers[handler_type].setFormatter(
                    ColorFormatter(message_format, '%H:%M:%S')
                )

    def set_logfile(self, filename: str) -> None:
        """
        Set logfile handler

        :param str filename: logfile file path
        """
        try:
            if filename == 'stdout':
                # special case, log usual log file contents to stdout
                handler = logging.StreamHandler(sys.__stdout__)
            else:
                handler = logging.FileHandler(
                    filename=filename, encoding='utf-8'
                )
                self.logfile = filename
            handler.setFormatter(
                logging.Formatter(
                    '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
                    '%H:%M:%S'
                )
            )
            handler.addFilter(LoggerSchedulerFilter())
            self.addHandler(handler)
            self.log_handlers['file'] = handler
        except Exception as e:
            raise KiwiLogFileSetupFailed(
                '%s: %s' % (type(e).__name__, format(e))
            )

    def set_log_socket(self, filename: str) -> None:
        """
        Set log socket handler

        :param str filename:
            UDS socket file path. Note if there is no server
            listening on the socket the log handler setup
            will fail
        """
        try:
            handler = PlainTextSocketHandler(filename, None)
            handler.makeSocket()
            handler.setFormatter(
                logging.Formatter(
                    '[ %(levelname)-8s]: %(asctime)-8s | %(message)s',
                    '%H:%M:%S'
                )
            )
            handler.addFilter(LoggerSchedulerFilter())
            self.addHandler(handler)
            self.log_handlers['socket'] = handler
        except Exception as e:
            raise KiwiLogSocketSetupFailed(
                'UDS socket: {0}:{1}: {2}'.format(filename, type(e).__name__, e)
            )

    def get_logfile(self) -> Optional[str]:
        """
        Return file path name of logfile

        :return: file path

        :rtype: str
        """
        return self.logfile

    @staticmethod
    def progress(
        current: int, total: int, prefix: str, bar_length: int = 40
    ) -> None:
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
        self.log_handlers[handler_type] = handler
