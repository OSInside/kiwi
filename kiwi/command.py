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
from typing import IO, Callable, List, MutableMapping, NamedTuple, Optional, overload
import logging
import os
import select
import subprocess
import sys

if sys.version_info >= (3, 8):
    from typing import Literal  # pragma: no cover
else:  # pragma: no cover
    from typing_extensions import Literal  # pragma: no cover

# project
from kiwi.utils.codec import Codec

from kiwi.exceptions import (
    KiwiCommandError,
    KiwiCommandNotFound
)

log = logging.getLogger('kiwi')


class CommandT(NamedTuple):
    output: str
    error: str
    returncode: int


class CommandCallT(NamedTuple):
    output: IO[bytes]
    output_available: Callable[[], bool]
    error: IO[bytes]
    error_available: Callable[[], bool]
    process: subprocess.Popen


class Command:
    """
    **Implements command invocation**

    An instance of Command provides methods to invoke external
    commands in blocking and non blocking mode. Control of
    stdout and stderr is given to the caller
    """

    @overload
    @staticmethod
    def run(
        command: List[str], custom_env: Optional[MutableMapping[str, str]] = None,
        raise_on_error: bool = True, stderr_to_stdout: bool = False,
        raise_on_command_not_found: Literal[False] = False
    ) -> CommandT:
        ...  # pragma: no cover

    @overload
    @staticmethod
    def run(
        command: List[str], custom_env: Optional[MutableMapping[str, str]] = None,
        raise_on_error: bool = True, stderr_to_stdout: bool = False,
        raise_on_command_not_found: bool = True
    ) -> Optional[CommandT]:
        ...  # pragma: no cover

    @staticmethod
    def run(
        command: List[str], custom_env: Optional[MutableMapping[str, str]] = None,
        raise_on_error: bool = True, stderr_to_stdout: bool = False,
        raise_on_command_not_found: bool = True
    ) -> Optional[CommandT]:
        """
        Execute a program and block the caller. The return value
        is a CommandT namedtuple containing the stdout, stderr
        and return code information. Unless raise_on_error is
        set to `False` an exception is thrown if the command
        exits with an error code not equal to zero. If
        raise_on_command_not_found is `False` and the command is
        not found, then `None` is returned.

        Example:

        .. code:: python

            result = Command.run(['ls', '-l'])

        :param list command: command and arguments
        :param dict custom_env: custom os.environ
        :param bool raise_on_error: control error behaviour
        :param bool stderr_to_stdout: redirects stderr to stdout

        :return:
            Contains call results in command type

            .. code:: python

                CommandT(output='string', error='string', returncode=int)

        :rtype: CommandT
        """
        from .path import Path
        environment = custom_env or os.environ
        cmd_abspath: Optional[str]
        if command[0].startswith("/"):
            cmd_abspath = command[0]
            if not os.path.exists(cmd_abspath):
                cmd_abspath = None
        else:
            cmd_abspath = Path.which(
                command[0], custom_env=environment, access_mode=os.X_OK
            )

        if not cmd_abspath:
            message = 'Command "%s" not found in the environment' % command[0]
            if raise_on_command_not_found:
                raise KiwiCommandNotFound(message)
            log.debug('EXEC: %s', message)
            return None
        stderr = subprocess.STDOUT if stderr_to_stdout else subprocess.PIPE
        log.debug('EXEC: [%s]', ' '.join(command))
        try:
            process = subprocess.Popen(
                [cmd_abspath] + command[1:],
                stdout=subprocess.PIPE,
                stderr=stderr,
                env=environment
            )
        except (OSError, subprocess.SubprocessError) as e:
            raise KiwiCommandError(
                '%s: %s: %s' % (command[0], type(e).__name__, format(e))
            ) from e

        output, error = process.communicate()
        if process.returncode != 0 and raise_on_error:
            if not error:
                error = bytes(b'(no output on stderr)')
            if not output:
                output = bytes(b'(no output on stdout)')
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
        return CommandT(
            output=Codec.decode(output),
            error=Codec.decode(error),
            returncode=process.returncode
        )

    @staticmethod
    def call(
            command: List[str],
            custom_env: Optional[MutableMapping[str, str]] = None
    ) -> CommandCallT:
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
        from .path import Path
        log.debug('EXEC: [%s]', ' '.join(command))
        environment = custom_env or os.environ
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
            ) from e

        # guaranteed to be true as stdout & stderr equal subprocess.PIPE
        assert process.stdout and process.stderr

        def output_available() -> Callable[[], bool]:
            def _select():
                readable, _, exceptional = select.select(
                    [process.stdout], [], [process.stdout], 1e-4
                )
                if readable and not exceptional:
                    return True
                return False
            return _select

        def error_available() -> Callable[[], bool]:
            def _select():
                readable, _, exceptional = select.select(
                    [process.stderr], [], [process.stderr], 1e-4
                )
                if readable and not exceptional:
                    return True
                return False
            return _select

        return CommandCallT(
            output=process.stdout,
            output_available=output_available(),
            error=process.stderr,
            error_available=error_available(),
            process=process
        )
