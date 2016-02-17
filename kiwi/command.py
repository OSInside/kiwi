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
import select
import os
import subprocess
from collections import namedtuple

# project
from .exceptions import KiwiCommandError


class Command(object):
    """
        Implements command invocation
    """
    @classmethod
    def run(self, command, custom_env=None, raise_on_error=True):
        """
            Execute a program and block the caller. The return value
            is a hash containing the stdout, stderr and return code
            information. Unless raise_on_error is set to false an
            exception is thrown if the command exits with an error
            code not equal to zero
        """
        from .logger import log
        log.debug('EXEC: [%s]', ' '.join(command))
        environment = os.environ
        if custom_env:
            environment = custom_env
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment
            )
        except Exception as e:
            raise KiwiCommandError(
                '%s: %s: %s' % (command[0], type(e).__name__, format(e))
            )
        output, error = process.communicate()
        if process.returncode != 0 and raise_on_error:
            log.debug('EXEC: Failed with %s', error)
            raise KiwiCommandError(
                '%s: %s' % (command[0], error)
            )
        command = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        return command(
            output=output.decode(),
            error=error.decode(),
            returncode=process.returncode
        )

    @classmethod
    def call(self, command, custom_env=None):
        """
            Execute a program and return an io file handle pair back.
            stdout and stderr are both on different channels. The caller
            must read from the output file handles in order to actually
            run the command. This can be done as follows:

            cmd = Command.call(...)

            errors = ''
            while cmd.process.poll() is None:
                while cmd.output_available():
                    data = cmd.output.readline()
                    if not data:
                        break
                    print data
                while cmd.error_available():
                    error = cmd.error.readline()
                    if not error:
                        break
                    errors += error

            if cmd.process.returncode != 0:
                print 'something failed: %s' % errors
        """
        from .logger import log
        log.debug('EXEC: [%s]', ' '.join(command))
        environment = os.environ
        if custom_env:
            environment = custom_env
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment
            )
        except Exception as e:
            raise KiwiCommandError(
                '%s: %s' % (type(e).__name__, format(e))
            )

        def output_available():
            def __select():
                descriptor_lists = select.select(
                    [process.stdout], [], [process.stdout], 1e-4
                )
                readable = descriptor_lists[0]
                exceptional = descriptor_lists[2]
                if readable and not exceptional:
                    return True
            return __select

        def error_available():
            def __select():
                descriptor_lists = select.select(
                    [process.stderr], [], [process.stderr], 1e-4
                )
                readable = descriptor_lists[0]
                exceptional = descriptor_lists[2]
                if readable and not exceptional:
                    return True
            return __select

        command = namedtuple(
            'command', [
                'output', 'output_available',
                'error', 'error_available',
                'process'
            ]
        )
        return command(
            output=process.stdout,
            output_available=output_available(),
            error=process.stderr,
            error_available=error_available(),
            process=process
        )
