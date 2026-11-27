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
from typing import Any, NamedTuple, List, Callable, Optional
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Column

# project
from kiwi.utils.codec import Codec
from kiwi.logger_console import KiwiConsole, get_progress_indent
from kiwi.utils.install_progress import InstallProgress, PackageManagerEventT

from kiwi.exceptions import KiwiCommandError

log: Any = logging.getLogger('kiwi')


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

    def __init__(
        self, command: CommandCallT, log_topic: str = 'system'
    ) -> None:
        self.command = CommandIterator(command)
        self.log_topic = log_topic

    def poll(self) -> None:
        """
        Iterate over process, raise on error and log output
        """
        for lineT in self.command:
            line = lineT.stdout_line
            if line:
                log.debug('%s: %s', self.log_topic, line)
        if self.command.get_error_code() != 0:
            raise KiwiCommandError(self.command.get_error_output())

    def poll_show_progress(
        self,
        event_method: Callable[[str], Optional[PackageManagerEventT]],
        progress_phases: List[str],
        with_stderr: bool = False,
    ) -> None:
        """
        Iterate over process and show progress in percent
        raise on error and log output

        The event method reads progress events from the process
        output, e.g the download and installation of a package or a
        running package script, see InstallProgress

        :param function event_method: method reading progress events
        :param list progress_phases: phases counted by the progress
        :param bool with_stderr: read the stderr output too
        """
        install_progress = InstallProgress(progress_phases)
        with Progress(
            TextColumn(
                get_progress_indent(*log.get_tree_position()), style='dim'
            ),
            SpinnerColumn(),
            TextColumn(
                '{task.description}',
                table_column=Column(
                    width=48, no_wrap=True, overflow='ellipsis'
                ),
            ),
            BarColumn(),
            TaskProgressColumn(),
            console=KiwiConsole.stdout,
            transient=True,
            # a progress display on a console which is not a terminal
            # is not updated, the summary is logged instead
            disable=not KiwiConsole.stdout.is_terminal,
        ) as progress:
            task = progress.add_task('Processing', total=InstallProgress.TOTAL)
            for lineT in self.command:
                lines = [lineT.stdout_line]
                if with_stderr:
                    lines.append(lineT.stderr_line)
                for line in lines:
                    if not line:
                        continue
                    log.debug('%s: %s', self.log_topic, line)
                    event = event_method(line)
                    if event:
                        install_progress.update(event)
                        progress.update(
                            task,
                            description=install_progress.description
                            or 'Processing',
                            completed=install_progress.completed,
                        )
            # the process is done
            progress.update(task, completed=InstallProgress.TOTAL)
        summary = install_progress.summary()
        if summary:
            log.info(f'{summary}')
        if self.command.get_error_code() != 0:
            raise KiwiCommandError(self.command.get_error_output())

    def poll_and_watch(self) -> Any:
        """
        Iterate over process don't raise on error and log
        stdout and stderr
        """
        log.debug(self.log_topic)
        log.debug('--------------out start-------------')
        for lineT in self.command:
            line = lineT.stdout_line
            if line:
                log.debug(line)
        log.debug('--------------out stop--------------')

        error_code = self.command.get_error_code()
        error_output = self.command.get_error_output()
        result = namedtuple('result', ['stderr', 'returncode'])
        if error_output:
            log.debug('--------------err start-------------')
            for line in error_output.split(os.linesep):
                log.debug(line)
            log.debug('--------------err stop--------------')
        return result(stderr=error_output, returncode=error_code)

    def returncode(self) -> int:
        return self.command.get_error_code()


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

        return PollT(stdout_line=line_stdout, stderr_line=line_stderr)

    def get_error_output(self) -> str:
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

    def __iter__(self) -> 'CommandIterator':
        return self
