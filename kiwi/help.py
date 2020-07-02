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
import subprocess

# project
from .exceptions import KiwiHelpNoCommandGiven


class Help:
    """
    **Implements man page help for kiwi commands**

    Each kiwi command implements their own manual page, which is
    shown if the positional argument 'help' is passed to the
    command.
    """
    def show(self, command=None):
        """
        Call man to show the command specific manual page

        All kiwi commands store their manual page in the section '8'
        of the man system. The calling process is replaced by the
        man process

        :param string command: man page name
        """
        if not command:
            raise KiwiHelpNoCommandGiven("No help context specified")
        subprocess.call('man 8 ' + command, shell=True)
