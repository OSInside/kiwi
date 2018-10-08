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

# In python2 bytes is string which is different from
# the bytes type in python3. The bytes type from the
# builtins generalizes this type to be bytes always
from builtins import bytes

# project
from .utils.codec import Codec

from .exceptions import (
    KiwiCommandError,
    KiwiCommandNotFound
)


class Command(object):
    """
    **Implements command invocation**

    An instance of Command provides methods to invoke external
    commands in blocking and non blocking mode. Control of
    stdout and stderr is given to the caller
    """
    @classmethod
    def run(self, command, custom_env=None, raise_on_error=True):
        """
        Execute a program and block the caller. The return value
        is a hash containing the stdout, stderr and return code
        information. Unless raise_on_error is set to false an
        exception is thrown if the command exits with an error
        code not equal to zero

        Example:

        .. code:: python

            result = Command.run(['ls', '-l'])

        :param list command: command and arguments
        :param list custom_env: custom os.environ
        :param bool raise_on_error: control error behaviour

        :return:
            Contains call results in command type

            .. code:: python

                command(output='string', error='string', returncode=int)

        :rtype: namedtuple
        """
        from .logger import log
        from .path import Path
        command_type = namedtuple(
            'command', ['output', 'error', 'returncode']
        )
        log.debug('EXEC: [%s]', ' '.join(command))
        environment = os.environ
        if custom_env:
            environment = custom_env
        if not Path.which(
            command[0], custom_env=environment, access_mode=os.X_OK
        ):
            message = 'Command "%s" not found in the environment' % command[0]
            if not raise_on_error:
                log.debug('EXEC: %s', message)
                return command_type(
                    output=None,
                    error=None,
                    returncode=-1
                )
            else:
                raise KiwiCommandNotFound(message)
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
        if process.returncode != 0 and not error:
            error = bytes(b'(no output on stderr)')
        if process.returncode != 0 and not output:
            output = bytes(b'(no output on stdout)')
        if process.returncode != 0 and raise_on_error:
            log.debug(
                'EXEC: Failed with stderr: {0}, stdout: {1}'.format(
                    Codec.decode(error), Codec.decode(output)
                )
            )
            raise KiwiCommandError(
                '{0}: stderr: {1}, stdout: {2}'.format(
                    command[0], Codec.decode(error), Codec.decode(output)
                )
            )
        return command_type(
            output=Codec.decode(output),
            error=Codec.decode(error),
            returncode=process.returncode
        )

    @classmethod
    def call(self, command, custom_env=None):
        """
        Execute a program and return an io file handle pair back.
        stdout and stderr are both on different channels. The caller
        must read from the output file handles in order to actually
        run the command. This can be done using the CommandIterator
        from command_process

        Example:

        .. code:: python

            process = Command.call(['ls', '-l'])

        :param list command: command and arguments
        :param list custom_env: custom os.environ

        :return:
            Contains process results in command type

            .. code:: python

                command(
                    output='string', output_available=bool,
                    error='string', error_available=bool,
                    process=subprocess
                )

        :rtype: namedtuple
        """
        from .logger import log
        from .path import Path
        log.debug('EXEC: [%s]', ' '.join(command))
        environment = os.environ
        if custom_env:
            environment = custom_env
        if not Path.which(
            command[0], custom_env=environment, access_mode=os.X_OK
        ):
            raise KiwiCommandNotFound(
                'Command "%s" not found in the environment' % command[0]
            )
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
            def _select():
                descriptor_lists = select.select(
                    [process.stdout], [], [process.stdout], 1e-4
                )
                readable = descriptor_lists[0]
                exceptional = descriptor_lists[2]
                if readable and not exceptional:
                    return True
            return _select

        def error_available():
            def _select():
                descriptor_lists = select.select(
                    [process.stderr], [], [process.stderr], 1e-4
                )
                readable = descriptor_lists[0]
                exceptional = descriptor_lists[2]
                if readable and not exceptional:
                    return True
            return _select

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
