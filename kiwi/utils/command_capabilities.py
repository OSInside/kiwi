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
import re
import logging
from typing import List

# project
from kiwi.command import Command
from kiwi.exceptions import KiwiCommandCapabilitiesError

log = logging.getLogger('kiwi')


class CommandCapabilities:
    """
    **Validation of command version flags or version**

    Performs commands calls and parses the output
    so it can look specific flags on help message, check
    command version, etc.
    """
    @staticmethod
    def has_option_in_help(
        call: str, flag: str, help_flags: List[str] = [],
        root: str = '', raise_on_error: bool = True, silent: bool = False
    ):
        """
        Checks if the given flag is present in the help output
        of the given command.

        :param str call: the command the check
        :param str flag: the flag or substring to find in stdout
        :param list help_flags: a list with the required command arguments.
        :param str root: root directory of the env to validate
        :param bool raise_on_error:
            raises KiwiCommandCapabilitiesError and message if the
            specified flag does not occur on stdout/stderr of the
            command call
        :param bool silent: don't log parsing failures

        :return: True if the flag is found, False in any other case

        :rtype: bool
        """
        help_args = help_flags or ['--help']
        if root:
            arguments = ['chroot', root, call] + help_args
        else:
            arguments = [call] + help_args
        command = Command.run(arguments, raise_on_error=False)
        for line in command.output.splitlines():
            if flag in line:
                return True
        for line in command.error.splitlines():
            if flag in line:
                return True
        message = 'Could not parse {} output'.format(call)
        if raise_on_error:
            raise KiwiCommandCapabilitiesError(message)
        if not silent:
            log.warning(message)
        return False

    @staticmethod
    def check_version(
        call: str, version_waterline: tuple, version_flags: List[str] = [],
        root: str = '', raise_on_error: bool = True, silent: bool = False
    ) -> bool:
        """
        Checks if the given command version is equal or higher than
        the given version tuple.

        :param str call: the command the check
        :param tuple version_waterline: minimum desired version of the command
        :param list version_flags: a list with the required command arguments.
        :param str root: root directory of the env to validate
        :param bool raise_on_error: control error behavior
        :param bool silent: don't log parsing failures

        :raises KiwiCommandCapabilitiesError: if raise_on_error is True and
            command execution fails or version can't be parsed.
        :return: True if the current command version is equal or higher to
            version_waterline

        :rtype: bool
        """
        version_args = version_flags or ['--version']
        if root:
            arguments = ['chroot', root, call] + version_args
        else:
            arguments = [call] + version_args
        version_info = None
        try:
            command = Command.run(arguments)
            for line in command.output.splitlines():
                matches = re.findall(r'([0-9]+(\.[0-9]+)*)', line)
                if matches:
                    match = max([m[0] for m in matches], key=len)
                    version_info = tuple(
                        int(elt) for elt in match.split('.')
                    )
                    break
            if version_info is None:
                raise Exception
        except Exception:
            message = 'Could not parse {0} version'.format(call)
            if raise_on_error:
                raise KiwiCommandCapabilitiesError(message)
            if not silent:
                log.warning(message)
            return False
        return version_info >= version_waterline
