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
from command import Command
from tempfile import NamedTemporaryFile
from defaults import Defaults


class Shell(object):
    """
        special character handling for shell evaluated code
    """
    @classmethod
    def quote(self, message):
        """
            quote characters which have a special meaning for bash
            but should be used as normal characters. actually I had
            planned to use pipes.quote but it does not quote as I
            had expected it. e.g 'name_wit_a_$' does not quote the $
            so we do it on our own for the scope of kiwi
        """
        # \\ quoting must be first in the list
        quote_characters = ['\\', '$', '"', '`', '!']
        for quote in quote_characters:
            message = message.replace(quote, '\\' + quote)
        return message

    @classmethod
    def quote_key_value_file(self, filename):
        """
            quote given input file which has to be of the form
            key=value to be able to become sourced by the shell
        """
        temp_copy = NamedTemporaryFile()
        Command.run(['cp', filename, temp_copy.name])
        Shell.run_common_function('baseQuoteFile', [temp_copy.name])
        with open(temp_copy.name) as quoted:
            return quoted.read().splitlines()

    @classmethod
    def run_common_function(self, name, parameters):
        Command.run([
            'bash', '-c',
            'source ' + Defaults.get_common_functions_file() +
            '; ' + name + ' ' + ' '.join(parameters)
        ])
