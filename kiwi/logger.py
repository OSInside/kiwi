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
from contextlib import contextmanager
from typing import Dict, Iterator, Optional, List, Tuple
import logging
import time
from kiwi.logger_socket import PlainTextSocketHandler
import sys

# project
from kiwi.logger_console import (
    ConsoleHandler,
    ConsoleRenderer,
    format_duration,
)
from kiwi.logger_filter import (
    LoggerSchedulerFilter,
    InfoFilter,
    DebugFilter,
    ErrorFilter,
    WarningFilter,
)

from kiwi.exceptions import KiwiLogFileSetupFailed, KiwiLogSocketSetupFailed


class Logger(logging.Logger):
    """
    **Extended logging facility based on Python logging**

    :param str name: name of the logger
    """

    def __init__(self, name: str):
        logging.Logger.__init__(self, name)
        self.log_handlers: Dict = {}
        self.logfile: Optional[str] = None
        self.step_depth = 0
        self.phase_active = False
        renderer = ConsoleRenderer(self.get_tree_position)
        # log INFO to stdout
        self._add_console_handler(
            'info', renderer, [InfoFilter(), LoggerSchedulerFilter()]
        )
        # log WARNING messages to stdout
        self._add_console_handler('warning', renderer, [WarningFilter()])
        # log DEBUG messages to stdout
        self._add_console_handler('debug', renderer, [DebugFilter()])
        # log ERROR messages to stderr
        self._add_console_handler('error', renderer, [ErrorFilter()], 'stderr')
        self.log_level = self.level
        self.log_flags: Dict[str, bool] = {}

    def phase(self, title: str) -> None:
        """
        Log the start of a phase of the build process, e.g the
        preparation of the root system. On the console the phase
        is shown as a headline

        :param str title: name of the phase
        """
        self.info(title, extra={'kiwi_role': 'phase'})
        self.phase_active = True

    def get_tree_position(self) -> Tuple[bool, int]:
        """
        Position of the next message in the console output tree

        :return: phase is active and number of active steps

        :rtype: tuple
        """
        return (self.phase_active, self.step_depth)

    def item(
        self, key: str, value: str, checked: Optional[bool] = None
    ) -> None:
        """
        Log an item of an information list, e.g the image summary.
        On the console the items are shown as a table with the key
        in the first column, consecutive items of the same key show
        the key only once. An item with a checked state is shown as
        a check list entry

        :param str key: name of the item, e.g Repositories
        :param str value: value of the item
        :param bool checked: state of a check list entry
        """
        mark = ''
        if checked is not None:
            mark = '[x] ' if checked else '[ ] '
        self.info(
            f'{key}: {mark}{value}',
            extra={
                'kiwi_role': 'item',
                'kiwi_key': key,
                'kiwi_value': value,
                'kiwi_checked': checked,
            },
        )

    @contextmanager
    def step(self, title: str) -> Iterator[None]:
        """
        Log a step of the build process

        The start and the end of the step are logged, including the
        time the step took. On the console the messages logged
        within the step are shown indented below the step

        .. code:: python

            with log.step('Installing bootstrap packages'):
                ...

        :param str title: name of the step
        """
        started = time.monotonic()
        self.info(title, extra={'kiwi_role': 'step_start'})
        self.step_depth += 1
        try:
            yield
        except BaseException:
            self._end_step(title, started, failed=True)
            raise
        self._end_step(title, started)

    def _end_step(
        self, title: str, started: float, failed: bool = False
    ) -> None:
        self.step_depth = max(self.step_depth - 1, 0)
        duration = time.monotonic() - started
        self.info(
            '{0}: {1} ({2})'.format(
                title, 'failed' if failed else 'done', format_duration(duration)
            ),
            extra={
                'kiwi_role': 'step_failed' if failed else 'step_done',
                'kiwi_title': title,
                'kiwi_duration': duration,
            },
        )

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
                    '%H:%M:%S',
                )
            )
            handler.addFilter(LoggerSchedulerFilter())
            self.addHandler(handler)
            self.log_handlers['file'] = handler
        except Exception as e:
            raise KiwiLogFileSetupFailed(f'{type(e).__name__}: {format(e)}')

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
                    '%H:%M:%S',
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

    def _add_console_handler(
        self,
        handler_type: str,
        renderer: ConsoleRenderer,
        message_filter: List[logging.Filter],
        channel: str = 'stdout',
    ) -> None:
        handler = ConsoleHandler(renderer, channel)
        for rule in message_filter:
            handler.addFilter(rule)
        self.addHandler(handler)
        self.log_handlers[handler_type] = handler
