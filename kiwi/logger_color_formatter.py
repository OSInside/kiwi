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


class ColorMessage:
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

    def format_message(self, level: str, message: str) -> str:
        """
        Message formatter with support for embedded color sequences

        The Message is allowed to contain the following color metadata:

        * $RESET, reset to no color mode
        * $BOLD, bold
        * $COLOR, color the following text
        * $LIGHTCOLOR, light color the following text

        The color of the message depends on the level and is defined
        in the ColorMessage constructor

        :param str level: color level name
        :param str message: text

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
    def format(self, record: logging.LogRecord) -> str:
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
