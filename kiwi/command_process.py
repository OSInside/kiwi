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
import os
import logging
from collections import namedtuple
from kiwi.command import CommandCallT
from typing import (
    NamedTuple, List, Callable
)

# project
from kiwi.utils.codec import Codec
from kiwi.logger import Logger

from kiwi.exceptions import KiwiCommandError

log = logging.getLogger('kiwi')


class PollT(NamedTuple):
    stdout_line: str
    stderr_line: str


class CommandProcess:
    """
    **Implements processing of non blocking Command calls**

    Provides methods to iterate over non blocking instances of
    the Command class with and without progress information

    :param subprocess command: instance of subprocess
    :param string log_topic: topic string for logging
    """
    def __init__(self, command: CommandCallT, log_topic='system') -> None:
        self.command = CommandIterator(command)
        self.log_topic = log_topic
        self.items_processed = 0

    def poll(self):
        """
        Iterate over process, raise on error and log output
        """
        for lineT in self.command:
            line = lineT.stdout_line
            if line:
                log.debug('%s: %s', self.log_topic, line)
        if self.command.get_error_code() != 0:
            raise KiwiCommandError(
                self.command.get_error_output()
            )

    def poll_show_progress(
        self, items_to_complete: List[str], match_method: Callable,
        with_stderr: bool = False
    ):
        """
        Iterate over process and show progress in percent
        raise on error and log output

        :param list items_to_complete: all items
        :param function match_method: method matching item
        """
        self._init_progress()
        for lineT in self.command:
            lines = [lineT.stdout_line]
            if with_stderr:
                lines.append(lineT.stderr_line)
            for line in lines:
                if line:
                    log.debug('%s: %s', self.log_topic, line)
                    self._update_progress(
                        match_method, items_to_complete, line
                    )
        self._stop_progress()
        if self.command.get_error_code() != 0:
            raise KiwiCommandError(
                self.command.get_error_output()
            )

    def poll_and_watch(self):
        """
        Iterate over process don't raise on error and log
        stdout and stderr
        """
        log.info(self.log_topic)
        log.debug('--------------out start-------------')
        for lineT in self.command:
            line = lineT.stdout_line
            if line:
                log.debug(line)
        log.debug('--------------out stop--------------')

        error_code = self.command.get_error_code()
        error_output = self.command.get_error_output()
        result = namedtuple(
            'result', ['stderr', 'returncode']
        )
        if error_output:
            log.debug('--------------err start-------------')
            for line in error_output.split(os.linesep):
                log.debug(line)
            log.debug('--------------err stop--------------')
        return result(
            stderr=error_output, returncode=error_code
        )

    def create_match_method(self, method):
        """
        create a matcher function pointer which calls the given
        method as method(item_to_match, data) on dereference

        :param function method: function reference

        :return: function pointer
        :rtype: object
        """
        def create_method(item_to_match, data):
            return method(item_to_match, data)
        return create_method

    def returncode(self):
        return self.command.get_error_code()

    def _init_progress(self):
        Logger.progress(
            0, 100, '[ INFO    ]: Processing'
        )

    def _stop_progress(self):
        Logger.progress(
            100, 100, '[ INFO    ]: Processing'
        )

    def _update_progress(
        self, match_method, items_to_complete, command_output
    ):
        items_count = len(items_to_complete)
        for item in items_to_complete:
            if match_method(item, command_output):
                self.items_processed += 1
                if self.items_processed <= items_count:
                    Logger.progress(
                        self.items_processed, items_count,
                        '[ INFO    ]: Processing'
                    )


class CommandIterator:
    """
    **Implements an Iterator for Instances of Command**

    :param subprocess command: instance of subprocess
    """
    def __init__(self, command: CommandCallT) -> None:
        self.command = command
        self.command_error_output = bytes(b'')
        self.command_output_line = bytes(b'')
        self.command_error_line = bytes(b'')
        self.output_eof_reached = False
        self.errors_eof_reached = False

    def __next__(self) -> PollT:
        line_stdout = ''
        line_stderr = ''
        if self.command.process.poll() is not None:
            if self.output_eof_reached and self.errors_eof_reached:
                raise StopIteration()

        if self.command.output_available():
            byte_read = self.command.output.read(1)
            if not byte_read:
                self.output_eof_reached = True
            elif byte_read == bytes(b'\n'):
                line_stdout = Codec.decode(self.command_output_line)
                self.command_output_line = bytes(b'')
            else:
                self.command_output_line += byte_read

        if self.command.error_available():
            byte_read = self.command.error.read(1)
            if not byte_read:
                self.errors_eof_reached = True
            elif byte_read == bytes(b'\n'):
                line_stderr = Codec.decode(self.command_error_line)
                self.command_error_line = bytes(b'')
                self.command_error_output += byte_read
            else:
                self.command_error_line += byte_read
                self.command_error_output += byte_read

        return PollT(
            stdout_line=line_stdout,
            stderr_line=line_stderr
        )

    def get_error_output(self):
        """
        Provide data which was sent to the stderr channel

        :return: stderr data

        :rtype: str
        """
        return Codec.decode(self.command_error_output)

    def get_error_code(self) -> int:
        """
        Provide return value from processed command

        :return: errorcode

        :rtype: int
        """
        return self.command.process.returncode

    def get_pid(self) -> int:
        """
        Provide process ID of command while running

        :return: pid

        :rtype: int
        """
        return self.command.process.pid

    def kill(self) -> None:
        """
        Send kill signal SIGTERM to command process
        """
        self.command.process.kill()

    def __iter__(self):
        return self
