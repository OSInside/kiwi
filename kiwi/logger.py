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
from .exceptions import (
    KiwiLogFileSetupFailed
)


class ColorMessage(object):
    """
    **Implements color messages for Python logging facility**

    Has to implement the format_message method to serve as
    message formatter
    """
    def __init__(self):
        BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = list(range(8))
        self.color = {
            'BLACK': BLACK,
            'WARNING': YELLOW,
            'INFO': WHITE,
            'DEBUG': WHITE,
            'CRITICAL': YELLOW,
            'ERROR': RED,
            'RED': RED,
            'GREEN': GREEN,
            'YELLOW': YELLOW,
            'BLUE': BLUE,
            'MAGENTA': MAGENTA,
            'CYAN': CYAN,
            'WHITE': WHITE
        }
        self.esc = {
            'reset': '\033[0m',
            'color': '\033[3;%dm',
            'color_light': '\033[2;%dm',
            'bold': '\033[1m'
        }

    def format_message(self, level, message):
        """
        Message formatter with support for embedded color sequences

        The Message is allowed to contain the following color metadata:

        * $RESET, reset to no color mode
        * $BOLD, bold
        * $COLOR, color the following text
        * $LIGHTCOLOR, light color the following text

        The color of the message depends on the level and is defined
        in the ColorMessage constructor

        :param int level: color level number
        :param string message: text

        :return: color message with escape sequences

        :rtype: str
        """
        message = message.replace(
            '$RESET',
            self.esc['reset']
        ).replace(
            '$BOLD',
            self.esc['bold']
        ).replace(
            '$COLOR',
            self.esc['color'] % (30 + self.color[level])
        ).replace(
            '$LIGHTCOLOR',
            self.esc['color_light'] % (30 + self.color[level])
        )
        for color_name, color_id in list(self.color.items()):
            message = message.replace(
                '$' + color_name,
                self.esc['color'] % (color_id + 30)
            ).replace(
                '$BG' + color_name,
                self.esc['color'] % (color_id + 40)
            ).replace(
                '$BG-' + color_name,
                self.esc['color'] % (color_id + 40)
            )
        return message + self.esc['reset']


class ColorFormatter(logging.Formatter):
    """
    **Extended standard logging Formatter**

    Extended format supporting text with color metadata

    Example:

    .. code:: python

        ColorFormatter(message_format, '%H:%M:%S')
    """
    def __init__(self, *args, **kwargs):
        # can't do super(...) here because Formatter is an old school class
        logging.Formatter.__init__(self, *args, **kwargs)

    def format(self, record):
        """
        Creates a logging Formatter with support for color messages

        :param tuple record: logging message record

        :return: result from format_message
        :rtype: str
        """
        color = ColorMessage()
        levelname = record.levelname
        message = logging.Formatter.format(self, record)
        return color.format_message(levelname, message)


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


class Logger(logging.Logger):
    """
    **Extended logging facility based on Python logging**

    :param string name: name of the logger
    """
    def __init__(self, name):
        logging.Logger.__init__(self, name)
        self.console_handlers = {}
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
        except Exception as e:
            raise KiwiLogFileSetupFailed(
                '%s: %s' % (type(e).__name__, format(e))
            )

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


# Create an application global log instance
#
# Set the highest log level possible as the default log level
# in the main Logger class. This is needed to allow any logfile
# handler to log all messages by default and to allow custom log
# levels per handler. Our own implementation in Logger::setLogLevel
# will then set the log level on a handler basis

logging.setLoggerClass(Logger)
log = logging.getLogger("kiwi")

log.setLevel(logging.DEBUG)
