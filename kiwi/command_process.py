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
# project
from logger import log
from collections import namedtuple

from exceptions import (
    KiwiCommandError
)


class CommandProcess(object):
    """
        Implements processing of non blocking Command calls
        with and without progress information
    """
    def __init__(self, command, log_topic='system'):
        self.command = command
        self.log_topic = log_topic
        self.items_processed = 0

    def poll_show_progress(self, items_to_complete, match_method):
        self.__process_poll(
            raise_on_error=True, watch=False,
            items_to_complete=items_to_complete, match_method=match_method
        )

    def poll(self):
        self.__process_poll()

    def poll_and_watch(self):
        return self.__process_poll(
            raise_on_error=False, watch=True
        )

    def create_match_method(self, method):
        """
            create a matcher method with the following interface
            f(item_to_match, data)
        """
        def create_method(item_to_match, data):
            return method(item_to_match, data)
        return create_method

    def __process_poll(
        self, raise_on_error=True, watch=False,
        items_to_complete=None, match_method=None
    ):
        show_progress = False
        if items_to_complete:
            show_progress = True

        if show_progress:
            self.__init_progress()
        elif watch:
            log.info(self.log_topic)
            log.debug('--------------start--------------')

        command_error_output = ''
        command_output_buffer_line = ''
        while self.command.process.poll() is None:
            output_eof_reached = False
            errors_eof_reached = False
            while True:
                if self.command.output_available() and not output_eof_reached:
                    byte_read = self.command.output.read(1)
                    if not byte_read:
                        output_eof_reached = True
                    elif byte_read == '\n':
                        if watch:
                            log.debug(
                                command_output_buffer_line
                            )
                        else:
                            log.debug(
                                '%s: %s', self.log_topic,
                                command_output_buffer_line
                            )
                        if show_progress:
                            self.__update_progress(
                                match_method, items_to_complete,
                                command_output_buffer_line
                            )
                        command_output_buffer_line = ''
                    else:
                        command_output_buffer_line += byte_read

                if self.command.error_available() and not errors_eof_reached:
                    byte_read = self.command.error.read(1)
                    if not byte_read:
                        errors_eof_reached = True
                    else:
                        command_error_output += byte_read

                if output_eof_reached and errors_eof_reached:
                    break

        if show_progress:
            self.__stop_progress()
        elif watch:
            log.debug('--------------stop--------------')

        if raise_on_error and self.command.process.returncode != 0:
            raise KiwiCommandError(command_error_output)
        else:
            result = namedtuple(
                'result', ['stderr', 'returncode']
            )
            return result(
                stderr=command_error_output,
                returncode=self.command.process.returncode
            )

    def __init_progress(self):
        log.progress(
            0, 100, '[ INFO    ]: Processing'
        )

    def __stop_progress(self):
        log.progress(
            100, 100, '[ INFO    ]: Processing'
        )
        print

    def __update_progress(
        self, match_method, items_to_complete, command_output
    ):
        items_count = len(items_to_complete)
        for item in items_to_complete:
            if match_method(item, command_output):
                self.items_processed += 1
                if self.items_processed <= items_count:
                    log.progress(
                        self.items_processed, items_count,
                        '[ INFO    ]: Processing'
                    )

    def __del__(self):
        if self.command and self.command.process.returncode is None:
            log.info(
                'Terminating subprocess %d', self.command.process.pid
            )
            self.command.process.kill()
