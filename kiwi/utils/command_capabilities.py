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
from kiwi.command import Command
from kiwi.logger import log


class CommandCapabilities(object):
    """
    Performs commands calls and parses the output
    so it can look specific flags on help message, check
    command version, etc.
    """
    @classmethod
    def has_option_in_help(
        self, call, flag, help_flags=['--help'], root=None
    ):
        """
        Checks if the given flag is present in the help output
        of the given command.

        :param string call: the command the check
        :param string flag: the flag or substring to find in stdout
        :param list help_flags: a list with the required command arguments.
        :param string root: root directory of the env to validate

        :return: True if the flag is found, False in any other case
        :rtype: boolean
        """
        if root:
            arguments = ['chroot', root, call] + help_flags
        else:
            arguments = [call] + help_flags
        try:
            command = Command.run(arguments)
            for line in command.output.splitlines():
                if flag in line:
                    return True
        except Exception:
            log.warning('Could not parse {0} output'.format(call))
        return False
